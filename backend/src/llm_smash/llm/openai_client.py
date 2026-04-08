"""OpenAI-backed LLM adapter for battle turn selection."""

from __future__ import annotations

import asyncio
from importlib import import_module
import json
import random
import re
import time
from typing import Any, Awaitable, Callable

_THINK_TAG_PATTERN = re.compile(r"<think.*?>.*?</think\s*>", re.DOTALL)

from llm_smash.engine.state import BattleState, TurnLog
from llm_smash.fighters.roster import get_system_prompt
from llm_smash.llm.adapter import AdapterResult, LLMAdapter

openai = import_module("openai")


class OpenAIClient(LLMAdapter):
    """LLM adapter backed by the OpenAI async Python SDK."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    _TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.client: Any = None

    def _get_client(self) -> Any:
        if self.client is None:
            kwargs: dict[str, Any] = {
                "api_key": self.api_key,
                "timeout": self.timeout,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = openai.AsyncOpenAI(**kwargs)
        return self.client

    def _is_transient_api_error(self, exc: Exception) -> bool:
        if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
            return True
        status_code = getattr(exc, "status_code", None)
        return (
            isinstance(exc, openai.APIStatusError)
            and status_code in self._TRANSIENT_STATUS_CODES
        )

    async def _retry_api_call(
        self,
        coro_factory: Callable[[], Awaitable[Any]],
        retries: int = MAX_RETRIES,
    ) -> Any:
        for attempt in range(retries + 1):
            try:
                return await coro_factory()
            except Exception as exc:
                if attempt == retries or not self._is_transient_api_error(exc):
                    raise

                delay = self.BASE_DELAY * (2**attempt) + random.uniform(0.0, 0.5)
                await asyncio.sleep(delay)

        raise RuntimeError("Retry loop exited unexpectedly")

    async def get_post_match_comment(
        self,
        fighter_id: str,
        opponent_codename: str,
        result: str,
        model: str = "",
    ) -> str:
        """Generate a post-match comment using the live LLM."""
        if result == "victory":
            prompt = (
                f"You just won a match as {fighter_id} against {opponent_codename}. "
                "Give a 1-sentence victory speech using AI/ML/software jargon as a combat metaphor. "
                "Be witty, punchy, and confident. Roast the loser."
            )
        elif result == "defeat":
            prompt = (
                f"You just lost a match as {fighter_id} against {opponent_codename}. "
                "Give a 1-sentence gracious but bitter defeat comment using AI/ML/software jargon. "
                "Be self-deprecating but dignified."
            )
        else:
            prompt = (
                f"The match ended in a draw between you ({fighter_id}) and {opponent_codename}. "
                "Give a 1-sentence comment about the tie using AI/ML/software jargon. "
                "Be philosophical and witty."
            )

        try:
            completion = await self._retry_api_call(
                lambda: self._get_client().chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                )
            )
            content = completion.choices[0].message.content
            if not content:
                return ""
            # Strip chain-of-thought blocks some models emit
            content = _THINK_TAG_PATTERN.sub("", content).strip()
            return content.strip('"')
        except Exception:
            return ""

    async def get_action(
        self,
        state: BattleState,
        turn: int,
        fighter_id: str,
        recent_logs: list[TurnLog] | None = None,
    ) -> AdapterResult:
        started = time.perf_counter()
        messages = [
            {"role": "system", "content": get_system_prompt(fighter_id)},
            {
                "role": "user",
                "content": json.dumps(
                    state.to_fighter_perspective(fighter_id, recent_logs=recent_logs)
                ),
            },
        ]

        try:
            completion = await self._retry_api_call(
                lambda: self._get_client().chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
            )
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(
                raw_response=completion.choices[0].message.content,
                latency_ms=latency_ms,
            )
        except openai.APITimeoutError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(
                timed_out=True,
                latency_ms=latency_ms,
                error=str(exc),
            )
        except (openai.APIError, openai.APIConnectionError) as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(latency_ms=latency_ms, error=str(exc))

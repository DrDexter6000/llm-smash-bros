"""OpenAI-backed LLM adapter for battle turn selection."""

from __future__ import annotations

from importlib import import_module
import json
import time
from typing import Any

from llm_smash.engine.state import BattleState, TurnLog
from llm_smash.fighters.roster import get_system_prompt
from llm_smash.llm.adapter import AdapterResult, LLMAdapter

openai = import_module("openai")


class OpenAIClient(LLMAdapter):
    """LLM adapter backed by the OpenAI async Python SDK."""

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
            completion = await self._get_client().chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
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

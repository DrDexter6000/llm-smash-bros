"""Anthropic-backed LLM adapter for live game turns."""

from __future__ import annotations

from importlib import import_module
import json
import time

from llm_smash.engine.state import BattleState, TurnLog
from llm_smash.fighters.roster import get_system_prompt
from llm_smash.llm.adapter import AdapterResult, LLMAdapter

anthropic = import_module("anthropic")
AsyncAnthropic = anthropic.AsyncAnthropic

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
JSON_ONLY_SUFFIX = (
    "\n\nRespond with ONLY valid JSON. No markdown, no explanation, no code blocks."
)


class AnthropicClient(LLMAdapter):
    """Anthropic adapter that requests a single JSON turn response."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        kwargs: dict[str, object] = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncAnthropic(**kwargs)

    async def get_action(
        self,
        state: BattleState,
        turn: int,
        fighter_id: str,
        recent_logs: list[TurnLog] | None = None,
    ) -> AdapterResult:
        del turn

        started = time.perf_counter()
        system_prompt = get_system_prompt(fighter_id)
        user_message = (
            json.dumps(
                state.to_fighter_perspective(fighter_id, recent_logs=recent_logs)
            )
            + JSON_ONLY_SUFFIX
        )

        try:
            message = await self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(
                raw_response=message.content[0].text,
                latency_ms=latency_ms,
            )
        except anthropic.APITimeoutError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(
                timed_out=True,
                latency_ms=latency_ms,
                error=str(exc),
            )
        except (anthropic.APIConnectionError, anthropic.APIError) as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(latency_ms=latency_ms, error=str(exc))

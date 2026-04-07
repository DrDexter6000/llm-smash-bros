"""Adapter interface for LLM-backed turn selection."""

from __future__ import annotations

import abc

from pydantic import BaseModel

from llm_smash.engine.state import BattleState, TurnLog


class AdapterResult(BaseModel):
    raw_response: str | None = None
    timed_out: bool = False
    latency_ms: float = 0.0
    error: str | None = None


class LLMAdapter(abc.ABC):
    """Abstract base class for LLM API clients."""

    @abc.abstractmethod
    async def get_action(
        self,
        state: BattleState,
        turn: int,
        fighter_id: str,
        recent_logs: list[TurnLog] | None = None,
    ) -> AdapterResult:
        """Return the raw JSON response for a fighter's turn."""
        raise NotImplementedError

    async def get_post_match_comment(
        self,
        fighter_id: str,
        opponent_codename: str,
        result: str,
        model: str = "",
    ) -> str:
        """Generate a post-match victory or defeat comment.

        Override in subclasses for live LLM calls. Default returns empty.
        result: "victory", "defeat", or "draw"
        """
        return ""

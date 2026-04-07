"""Utilities for compact recent-turn summaries in LLM prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from llm_smash.engine.state import TurnEvent, TurnLog


def summarize_turn(turn_log: TurnLog, fighter_id: str) -> dict[str, str | int]:
    """Summarize a turn from one fighter's perspective."""
    response = turn_log.actions.get(fighter_id)
    opponent_id = next((key for key in turn_log.actions if key != fighter_id), "")
    opponent_response = turn_log.actions.get(opponent_id)

    summary: dict[str, str | int] = {
        "turn": turn_log.turn_number,
        "you": _summarize_actor_turn(turn_log, fighter_id, response, target_self=False),
        "opponent": _summarize_actor_turn(
            turn_log,
            opponent_id,
            opponent_response,
            target_self=True,
        ),
    }

    notable = _summarize_notable(turn_log.events)
    if notable:
        summary["notable"] = notable
    return summary


def _summarize_actor_turn(
    turn_log: TurnLog,
    actor_id: str,
    response: Any,
    *,
    target_self: bool,
) -> str:
    if not actor_id or response is None:
        return "held position"

    if actor_id in turn_log.fumbles or _has_event(turn_log.events, "fumble", actor_id):
        return "fumbled"

    action_type = response.action.get("type")
    if action_type == "attack":
        ability_name = response.action.get("ability", "attack")
        damage = _find_damage_value(turn_log.events, source_id=actor_id)
        if damage > 0:
            suffix = " dmg to you" if target_self else " dmg"
            return (
                f"used {ability_name} → {damage}{suffix}"
                if target_self
                else f"attacked with {ability_name} → {damage}{suffix}"
            )
        return (
            f"used {ability_name}" if target_self else f"attacked with {ability_name}"
        )
    if action_type == "defend":
        return "defended"
    if action_type == "wait":
        return "waited (+5 energy)"
    return action_type or "acted"


def _summarize_notable(events: list[TurnEvent]) -> str:
    for event in events:
        if event.type in {"hazard", "ko"} and event.description:
            return event.description
    return ""


def _find_damage_value(events: list[TurnEvent], *, source_id: str) -> int:
    for event in events:
        if event.type == "damage" and event.source_id == source_id:
            return event.value
    return 0


def _has_event(events: list[TurnEvent], event_type: str, source_id: str) -> bool:
    return any(
        event.type == event_type and event.source_id == source_id for event in events
    )

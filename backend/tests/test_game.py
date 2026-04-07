"""Tests for the game engine match loop and lifecycle."""

from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

game_module = import_module("llm_smash.engine.game")
state_module = import_module("llm_smash.engine.state")
mock_client_module = import_module("llm_smash.llm.mock_client")

GameEngine = game_module.GameEngine
MatchConfig = game_module.MatchConfig
ActionType = state_module.ActionType
TurnLog = state_module.TurnLog
MockLLMClient = mock_client_module.MockLLMClient


def make_clients(
    fighter_ids: list[str],
    *,
    latency_ms: float = 0,
    failure_rate: float = 0.0,
    seed_base: int = 100,
) -> dict[str, MockLLMClient]:
    return {
        fighter_id: MockLLMClient(
            fighter_id=fighter_id,
            latency_ms=latency_ms,
            failure_rate=failure_rate,
            seed=seed_base + index,
        )
        for index, fighter_id in enumerate(fighter_ids)
    }


async def collect_turn(turn_log: TurnLog, sink: list[TurnLog]) -> None:
    sink.append(turn_log)


class TestGameEngine:
    @pytest.mark.asyncio
    async def test_match_runs_to_completion(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=12, seed=7),
            llm_clients=make_clients(fighter_ids, seed_base=10),
        )

        result = await engine.run_match()

        assert result.match_id
        assert result.total_turns >= 1
        assert result.end_reason in {"ko", "timeout", "draw"}
        assert result.winner in {None, *fighter_ids}
        assert result.is_draw is (result.winner is None)

    @pytest.mark.asyncio
    async def test_match_respects_max_turns(self):
        fighter_ids = ["gpt-4o", "gemini-1.5-pro"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=5, seed=13),
            llm_clients=make_clients(fighter_ids, seed_base=20),
        )

        result = await engine.run_match()

        assert result.total_turns <= 5
        if result.end_reason == "timeout":
            assert result.total_turns == 5

    @pytest.mark.asyncio
    async def test_match_ends_on_ko(self):
        fighter_ids = ["gpt-4o", "llama-3"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=30, seed=2),
            llm_clients=make_clients(fighter_ids, seed_base=30),
        )

        result = await engine.run_match()

        assert result.end_reason == "ko"
        assert result.winner in fighter_ids
        assert result.is_draw is False

    @pytest.mark.asyncio
    async def test_fumble_on_timeout(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        engine = GameEngine(
            MatchConfig(
                fighter_ids=fighter_ids,
                max_turns=3,
                timeout_per_turn=0.001,
                seed=5,
            ),
            llm_clients=make_clients(fighter_ids, latency_ms=50, seed_base=40),
        )

        result = await engine.run_match()

        assert result.total_fumbles >= 2
        assert any(turn.fumbles for turn in result.turn_log)

    @pytest.mark.asyncio
    async def test_fumble_on_invalid_response(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=3, seed=11),
            llm_clients=make_clients(
                fighter_ids,
                failure_rate=1.0,
                seed_base=50,
            ),
        )

        result = await engine.run_match()

        assert result.total_fumbles == result.total_turns * 2
        assert all(len(turn.fumbles) == 2 for turn in result.turn_log)

    @pytest.mark.asyncio
    async def test_turn_log_recorded(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=6, seed=17),
            llm_clients=make_clients(fighter_ids, seed_base=60),
        )

        result = await engine.run_match()

        assert len(result.turn_log) == result.total_turns
        assert [turn.turn_number for turn in result.turn_log] == list(
            range(1, result.total_turns + 1)
        )
        assert all(turn.state_after is not None for turn in result.turn_log)

    @pytest.mark.asyncio
    async def test_event_callback_called(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        seen_turns: list[TurnLog] = []

        async def event_callback(turn_log: TurnLog) -> None:
            await collect_turn(turn_log, seen_turns)

        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=6, seed=19),
            llm_clients=make_clients(fighter_ids, seed_base=70),
            event_callback=event_callback,
        )

        result = await engine.run_match()

        assert len(seen_turns) == result.total_turns
        assert [turn.turn_number for turn in seen_turns] == list(
            range(1, result.total_turns + 1)
        )

    @pytest.mark.asyncio
    async def test_hazards_spawn_during_match(self):
        fighter_ids = ["gpt-4o", "gemini-1.5-pro"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=10, seed=23),
            llm_clients=make_clients(fighter_ids, seed_base=80),
        )

        result = await engine.run_match()

        hazard_events = [
            event
            for turn in result.turn_log
            for event in turn.events
            if event.type == "hazard"
        ]
        assert result.total_turns >= 5
        assert hazard_events

    @pytest.mark.asyncio
    async def test_fumble_action_defaults_to_defend(self):
        fighter_ids = ["gpt-4o", "claude-3.5-sonnet"]
        engine = GameEngine(
            MatchConfig(fighter_ids=fighter_ids, max_turns=1, seed=29),
            llm_clients=make_clients(fighter_ids, failure_rate=1.0, seed_base=90),
        )

        turn_log = await engine._execute_turn(1)

        assert set(turn_log.fumbles) == set(fighter_ids)
        assert all(
            turn_log.actions[fighter_id] is not None
            and turn_log.actions[fighter_id].action["type"] == ActionType.DEFEND.value
            for fighter_id in fighter_ids
        )

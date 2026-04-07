"""Tests for the game engine match loop and lifecycle."""

from __future__ import annotations

import json
from importlib import import_module
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

game_module = import_module("llm_smash.engine.game")
state_module = import_module("llm_smash.engine.state")
mock_client_module = import_module("llm_smash.llm.mock_client")
adapter_module = import_module("llm_smash.llm.adapter")
roster_module = import_module("llm_smash.fighters.roster")

GameEngine = game_module.GameEngine
MatchConfig = game_module.MatchConfig
ActionType = state_module.ActionType
ActionResponse = state_module.ActionResponse
StatusEffect = state_module.StatusEffect
TurnLog = state_module.TurnLog
MockLLMClient = mock_client_module.MockLLMClient
AdapterResult = adapter_module.AdapterResult
LLMAdapter = adapter_module.LLMAdapter
get_fighter = roster_module.get_fighter


class StaticAdapter(LLMAdapter):
    def __init__(self, payload: dict[str, object]):
        self.payload = payload
        self.calls = 0

    async def get_action(self, state, turn: int, fighter_id: str) -> AdapterResult:
        del state, fighter_id
        self.calls += 1
        body = dict(self.payload)
        body["turn"] = turn
        return AdapterResult(raw_response=json.dumps(body))


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
        fighter_ids = ["striker", "guardian"]
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
        fighter_ids = ["guardian", "controller"]
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
        fighter_ids = ["striker", "berserker"]
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
        fighter_ids = ["striker", "guardian"]
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
        fighter_ids = ["striker", "guardian"]
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
        fighter_ids = ["striker", "guardian"]
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
        fighter_ids = ["striker", "guardian"]
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
        fighter_ids = ["guardian", "controller"]
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
        fighter_ids = ["striker", "guardian"]
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

    @pytest.mark.asyncio
    async def test_stunned_fighter_auto_defends_without_llm_call(self):
        stunned_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": None,
                "inner_monologue": "should not be used",
                "trash_talk": "",
            }
        )
        other_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": None,
                "inner_monologue": "waiting",
                "trash_talk": "",
            }
        )
        engine = GameEngine(
            MatchConfig(fighter_ids=["guardian", "controller"], max_turns=1, seed=31),
            llm_clients={"guardian": stunned_adapter, "controller": other_adapter},
        )
        engine._ensure_state()
        assert engine.state is not None
        stunned = engine.state.get_fighter("guardian")
        assert stunned is not None
        stunned.status_effects.append(
            StatusEffect(
                name="Stunned",
                turns_remaining=1,
                effect_type="stun",
            )
        )

        turn_log = await engine._execute_turn(1)

        assert stunned_adapter.calls == 0
        assert other_adapter.calls == 1
        assert turn_log.actions["guardian"] is not None
        assert turn_log.actions["guardian"].action["type"] == ActionType.DEFEND.value
        assert any(event.type == "stun" for event in turn_log.events)
        assert "guardian" not in turn_log.fumbles

    @pytest.mark.asyncio
    async def test_slowed_fighter_skips_movement(self):
        slow_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": {"direction": "left"},
                "inner_monologue": "stuck",
                "trash_talk": "",
            }
        )
        other_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": None,
                "inner_monologue": "waiting",
                "trash_talk": "",
            }
        )
        engine = GameEngine(
            MatchConfig(fighter_ids=["guardian", "controller"], max_turns=1, seed=37),
            llm_clients={"guardian": slow_adapter, "controller": other_adapter},
        )
        engine._ensure_state()
        assert engine.state is not None
        slowed = engine.state.get_fighter("guardian")
        assert slowed is not None
        starting_position = slowed.position.model_copy()
        slowed.status_effects.append(
            StatusEffect(name="Slowed", turns_remaining=1, effect_type="slow")
        )

        turn_log = await engine._execute_turn(1)

        assert slowed.position == starting_position
        assert any(event.type == "slow" for event in turn_log.events)

    @pytest.mark.asyncio
    async def test_attack_effects_apply_status_self_damage_and_knockback(self):
        attacker_adapter = StaticAdapter(
            {
                "action": {
                    "type": "attack",
                    "ability": "Repulsor",
                    "target": "striker",
                },
                "move": None,
                "inner_monologue": "push them back",
                "trash_talk": "",
            }
        )
        other_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": None,
                "inner_monologue": "waiting",
                "trash_talk": "",
            }
        )
        engine = GameEngine(
            MatchConfig(fighter_ids=["controller", "striker"], max_turns=1, seed=41),
            llm_clients={"controller": attacker_adapter, "striker": other_adapter},
        )
        engine._ensure_state()
        assert engine.state is not None
        controller = engine.state.get_fighter("controller")
        striker = engine.state.get_fighter("striker")
        assert controller is not None and striker is not None
        striker.position.x = 4
        striker.position.y = 3
        controller.position.x = 2
        controller.position.y = 3

        turn_log = await engine._execute_turn(1)

        assert striker.position.x == 6
        assert any(event.type == "knockback" for event in turn_log.events)

    @pytest.mark.asyncio
    async def test_self_damage_and_status_apply_from_berserker_ability(self):
        attacker_adapter = StaticAdapter(
            {
                "action": {
                    "type": "attack",
                    "ability": "Bloodlust",
                    "target": "guardian",
                },
                "move": None,
                "inner_monologue": "power up",
                "trash_talk": "",
            }
        )
        other_adapter = StaticAdapter(
            {
                "action": {"type": "wait"},
                "move": None,
                "inner_monologue": "waiting",
                "trash_talk": "",
            }
        )
        engine = GameEngine(
            MatchConfig(fighter_ids=["berserker", "guardian"], max_turns=1, seed=43),
            llm_clients={"berserker": attacker_adapter, "guardian": other_adapter},
        )
        engine._ensure_state()
        assert engine.state is not None
        berserker = engine.state.get_fighter("berserker")
        assert berserker is not None
        starting_hp = berserker.hp

        turn_log = await engine._execute_turn(1)

        assert berserker.hp == starting_hp - 10
        assert berserker.has_status("damage_boost")
        assert any(event.type == "status_applied" for event in turn_log.events)
        assert any(event.type == "self_damage" for event in turn_log.events)

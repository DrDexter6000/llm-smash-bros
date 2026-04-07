"""Tests for the LLM adapter interface and mock client."""

from __future__ import annotations

import json
from importlib import import_module
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

state_module = import_module("llm_smash.engine.state")
adapter_module = import_module("llm_smash.llm.adapter")
mock_client_module = import_module("llm_smash.llm.mock_client")

Ability = state_module.Ability
Arena = state_module.Arena
BattleState = state_module.BattleState
Fighter = state_module.Fighter
MatchPhase = state_module.MatchPhase
Position = state_module.Position
AdapterResult = adapter_module.AdapterResult
LLMAdapter = adapter_module.LLMAdapter
MockLLMClient = mock_client_module.MockLLMClient


@pytest.fixture
def sample_state() -> BattleState:
    f1 = Fighter(
        id="striker",
        codename="Striker",
        hp=80,
        max_hp=80,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Quick Strike",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            ),
            Ability(
                name="Execution",
                type="ultimate",
                damage=40,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=2,
            ),
        ],
    )
    f2 = Fighter(
        id="guardian",
        codename="Guardian",
        hp=120,
        max_hp=120,
        energy=80,
        max_energy=80,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Shield Bash",
                type="attack",
                damage=10,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            ),
        ],
    )
    arena = Arena(width=8, height=6)
    return BattleState(
        match_id="test",
        turn=1,
        phase=MatchPhase.FIGHTING,
        fighters=[f1, f2],
        arena=arena,
    )


def parse_response(result: AdapterResult) -> dict:
    assert result.raw_response is not None
    return json.loads(result.raw_response)


class TestAdapterContract:
    def test_adapter_result_defaults(self):
        result = AdapterResult()

        assert result.raw_response is None
        assert result.timed_out is False
        assert result.latency_ms == 0.0
        assert result.error is None

    def test_mock_client_implements_adapter_interface(self):
        client = MockLLMClient(fighter_id="striker")

        assert isinstance(client, LLMAdapter)


class TestMockLLMClient:
    @pytest.mark.asyncio
    async def test_returns_valid_json_string(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=7)

        result = await client.get_action(sample_state, turn=5, fighter_id="striker")
        payload = parse_response(result)

        assert payload["turn"] == 5
        assert "action" in payload
        assert "tactical_summary" in payload
        assert "trash_talk" in payload

    @pytest.mark.asyncio
    async def test_response_contains_correct_turn(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=3)

        result = await client.get_action(sample_state, turn=9, fighter_id="striker")
        payload = parse_response(result)

        assert payload["turn"] == 9

    @pytest.mark.asyncio
    async def test_response_contains_valid_action_type(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=11)

        result = await client.get_action(sample_state, turn=2, fighter_id="striker")
        payload = parse_response(result)

        assert payload["action"]["type"] in {"attack", "defend", "wait"}

    @pytest.mark.asyncio
    async def test_chosen_ability_is_available(self, sample_state: BattleState):
        fighter = sample_state.get_fighter("striker")
        assert fighter is not None
        fighter.get_ability("Execution").cooldown_remaining = 2
        fighter.energy = 10
        client = MockLLMClient(fighter_id="striker", seed=5)

        result = await client.get_action(sample_state, turn=4, fighter_id="striker")
        payload = parse_response(result)

        if payload["action"]["type"] == "attack":
            ability = fighter.get_ability(payload["action"]["ability"])
            assert ability is not None
            assert ability.is_available
            assert fighter.energy >= ability.energy_cost

    @pytest.mark.asyncio
    async def test_simulated_latency(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", latency_ms=200, seed=1)

        started = time.perf_counter()
        result = await client.get_action(sample_state, turn=3, fighter_id="striker")
        elapsed_ms = (time.perf_counter() - started) * 1000

        assert result.latency_ms >= 150
        assert elapsed_ms >= 150
        assert elapsed_ms < 1000

    @pytest.mark.asyncio
    async def test_failure_rate_produces_invalid_json(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", failure_rate=1.0, seed=2)

        result = await client.get_action(sample_state, turn=6, fighter_id="striker")

        with pytest.raises(json.JSONDecodeError):
            parse_response(result)

    @pytest.mark.asyncio
    async def test_seed_produces_deterministic_results(self, sample_state: BattleState):
        client_one = MockLLMClient(fighter_id="striker", seed=42)
        client_two = MockLLMClient(fighter_id="striker", seed=42)

        result_one = await client_one.get_action(
            sample_state, turn=7, fighter_id="striker"
        )
        result_two = await client_two.get_action(
            sample_state, turn=7, fighter_id="striker"
        )

        assert result_one.raw_response == result_two.raw_response

    @pytest.mark.asyncio
    async def test_adapter_result_has_latency_ms(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=9)

        result = await client.get_action(sample_state, turn=1, fighter_id="striker")

        assert result.latency_ms > 0
        assert result.timed_out is False
        assert result.error is None

    @pytest.mark.asyncio
    async def test_zero_failure_rate_always_valid(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", failure_rate=0.0, seed=21)

        for turn in range(1, 21):
            result = await client.get_action(
                sample_state, turn=turn, fighter_id="striker"
            )
            payload = parse_response(result)
            assert payload["turn"] == turn

    @pytest.mark.asyncio
    async def test_mock_handles_fighter_with_all_abilities_on_cooldown(
        self, sample_state: BattleState
    ):
        fighter = sample_state.get_fighter("striker")
        assert fighter is not None
        for ability in fighter.abilities:
            ability.cooldown_remaining = 3
        client = MockLLMClient(fighter_id="striker", seed=12)

        result = await client.get_action(sample_state, turn=8, fighter_id="striker")
        payload = parse_response(result)

        assert payload["action"]["type"] in {"defend", "wait"}

    @pytest.mark.asyncio
    async def test_attack_action_targets_opponent(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=7)

        for turn in range(1, 30):
            result = await client.get_action(
                sample_state, turn=turn, fighter_id="striker"
            )
            payload = parse_response(result)
            if payload["action"]["type"] == "attack":
                assert payload["action"]["target"] == "guardian"
                return

        pytest.fail("Expected at least one attack action in sampled turns")

    @pytest.mark.asyncio
    async def test_move_direction_is_valid_or_absent(self, sample_state: BattleState):
        client = MockLLMClient(fighter_id="striker", seed=8)

        result = await client.get_action(sample_state, turn=10, fighter_id="striker")
        payload = parse_response(result)
        move = payload.get("move")

        if move is not None:
            assert move["direction"] in {
                "up",
                "down",
                "left",
                "right",
                "up-left",
                "up-right",
                "down-left",
                "down-right",
            }

"""Tests for LLM response validation."""

import json

import pytest

from llm_smash.engine.state import (
    Ability,
    ActionResponse,
    Arena,
    BattleState,
    Fighter,
    MatchPhase,
    Position,
)
from llm_smash.engine.validator import ResponseValidator


@pytest.fixture
def validator() -> ResponseValidator:
    return ResponseValidator()


@pytest.fixture
def sample_state() -> BattleState:
    oracle = Fighter(
        id="gpt-4o",
        codename="The Oracle",
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=0, y=0),
        abilities=[
            Ability(
                name="Logic Missile",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=4,
            ),
            Ability(
                name="System Override",
                type="ultimate",
                damage=0,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=6,
                description="Hijacks the opponent's system prompt.",
            ),
        ],
        status_effects=[],
    )
    artisan = Fighter(
        id="claude-3.5-sonnet",
        codename="The Artisan",
        hp=85,
        max_hp=85,
        energy=100,
        max_energy=100,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Code Slice",
                type="attack",
                damage=14,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            )
        ],
        status_effects=[],
    )
    arena = Arena(width=8, height=6)
    return BattleState(
        match_id="test-match",
        turn=5,
        phase=MatchPhase.FIGHTING,
        fighters=[oracle, artisan],
        arena=arena,
    )


def make_raw_response(
    *,
    turn: int = 5,
    action: dict,
    move: dict | None = None,
    inner_monologue: str = "Time to strike.",
    trash_talk: str = "Your parameters are showing.",
) -> str:
    payload = {
        "turn": turn,
        "action": action,
        "move": move,
        "inner_monologue": inner_monologue,
        "trash_talk": trash_talk,
    }
    return json.dumps(payload)


class TestResponseValidator:
    def test_valid_json_attack_action_returns_parsed_response(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(
            action={
                "type": "attack",
                "ability": "Logic Missile",
                "target": "claude-3.5-sonnet",
            },
            move={"direction": "right"},
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert isinstance(result.response, ActionResponse)
        assert result.response.action["type"] == "attack"
        assert result.response.action["ability"] == "Logic Missile"
        assert result.response.action["target"] == "claude-3.5-sonnet"
        assert result.error is None

    def test_valid_json_defend_action_is_valid(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "defend"}, move=None)

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.action == {"type": "defend"}

    def test_valid_json_wait_action_is_valid(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "wait"}, move=None)

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.action == {"type": "wait"}

    def test_invalid_json_string_returns_json_error(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        result = validator.validate(
            '{"turn": 5, "action": ',
            turn=5,
            fighter_id="gpt-4o",
            state=sample_state,
        )

        assert result.is_valid is False
        assert result.response is None
        assert result.error is not None
        assert "json" in result.error.lower()

    def test_valid_json_with_missing_fields_fails_schema_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = json.dumps(
            {
                "turn": 5,
                "move": {"direction": "right"},
                "inner_monologue": "Oops.",
                "trash_talk": "Still invalid.",
            }
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.response is None
        assert result.error is not None

    def test_stale_turn_echo_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "wait"}, turn=4)

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "turn" in result.error.lower()

    def test_ability_on_cooldown_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        fighter = sample_state.get_fighter("gpt-4o")
        assert fighter is not None
        fighter.get_ability("System Override").cooldown_remaining = 3
        raw = make_raw_response(
            action={
                "type": "attack",
                "ability": "System Override",
                "target": "claude-3.5-sonnet",
            }
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "cooldown" in result.error.lower()

    def test_not_enough_energy_for_ability_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        fighter = sample_state.get_fighter("gpt-4o")
        assert fighter is not None
        fighter.energy = 20
        raw = make_raw_response(
            action={
                "type": "attack",
                "ability": "System Override",
                "target": "claude-3.5-sonnet",
            }
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "energy" in result.error.lower()

    def test_unknown_ability_name_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(
            action={
                "type": "attack",
                "ability": "Imaginary Technique",
                "target": "claude-3.5-sonnet",
            }
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "ability" in result.error.lower()

    def test_off_grid_movement_is_still_valid_for_validator(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(
            action={"type": "wait"},
            move={"direction": "up-left"},
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.move == {"direction": "up-left"}

    def test_attack_without_ability_field_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(
            action={"type": "attack", "target": "claude-3.5-sonnet"}
        )

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "ability" in result.error.lower()

    def test_attack_without_target_field_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "attack", "ability": "Logic Missile"})

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "target" in result.error.lower()

    def test_invalid_action_type_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "dance"})

        result = validator.validate(
            raw, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "action" in result.error.lower()

    def test_markdown_code_fences_are_stripped_before_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        fenced = "```json\n" + make_raw_response(action={"type": "wait"}) + "\n```"

        result = validator.validate(
            fenced, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.action == {"type": "wait"}

    def test_empty_string_is_invalid(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        result = validator.validate("", turn=5, fighter_id="gpt-4o", state=sample_state)

        assert result.is_valid is False
        assert result.response is None
        assert result.error is not None

    def test_unknown_fighter_id_fails_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        raw = make_raw_response(action={"type": "wait"})

        result = validator.validate(
            raw, turn=5, fighter_id="missing-fighter", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None
        assert "fighter" in result.error.lower()

    def test_think_tags_are_stripped_before_validation(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        inner_json = make_raw_response(action={"type": "wait"})
        wrapped = f"<think>\nLet me analyze the state...\n</think>\n{inner_json}"

        result = validator.validate(
            wrapped, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.action == {"type": "wait"}

    def test_think_tags_plus_markdown_fences_are_stripped(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        inner_json = make_raw_response(action={"type": "defend"})
        wrapped = (
            f"<think>\nI should defend here.\n</think>\n```json\n{inner_json}\n```"
        )

        result = validator.validate(
            wrapped, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is True
        assert result.response is not None
        assert result.response.action == {"type": "defend"}

    def test_think_tags_only_content_returns_empty_response(
        self, validator: ResponseValidator, sample_state: BattleState
    ):
        wrapped = "<think>\nJust thinking, no action.\n</think>"

        result = validator.validate(
            wrapped, turn=5, fighter_id="gpt-4o", state=sample_state
        )

        assert result.is_valid is False
        assert result.error is not None

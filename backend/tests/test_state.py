"""Tests for core state models."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from llm_smash.engine.state import (
    AbilityEffect,
    ActionResponse,
    Arena,
    BattleState,
    DIRECTION_VECTORS,
    Fighter,
    Hazard,
    MatchPhase,
    MoveDirection,
    Ability,
    Position,
    StatusEffect,
)


class TestPosition:
    def test_create_position(self):
        pos = Position(x=3, y=2)
        assert pos.x == 3 and pos.y == 2

    def test_distance_to_pythagorean(self):
        a = Position(x=0, y=0)
        b = Position(x=3, y=4)
        assert a.distance_to(b) == 5.0

    def test_distance_to_same_point(self):
        a = Position(x=5, y=5)
        assert a.distance_to(a) == 0.0

    def test_chebyshev_distance(self):
        a = Position(x=0, y=0)
        b = Position(x=3, y=4)
        assert a.chebyshev_distance(b) == 4

    def test_chebyshev_distance_diagonal(self):
        a = Position(x=0, y=0)
        b = Position(x=3, y=3)
        assert a.chebyshev_distance(b) == 3  # Diagonal = max(3, 3) = 3

    def test_equality(self):
        assert Position(x=1, y=2) == Position(x=1, y=2)
        assert Position(x=1, y=2) != Position(x=2, y=1)

    def test_hashable(self):
        positions = {Position(x=1, y=2), Position(x=1, y=2), Position(x=3, y=4)}
        assert len(positions) == 2


class TestAbility:
    def test_create_ability(self):
        ability = Ability(name="Fireball", type="attack", damage=20, range=3)
        assert ability.name == "Fireball"
        assert ability.damage == 20

    def test_ability_effects_default_to_empty_list(self):
        ability = Ability(name="Fortify", type="buff")
        assert ability.effects == []


class TestAbilityEffect:
    def test_create_status_apply_effect(self):
        effect = AbilityEffect(
            type="status_apply",
            target="self",
            status_name="Fortified",
            status_effect_type="damage_reduction",
            status_value=0.4,
            status_duration=2,
        )

        assert effect.type == "status_apply"
        assert effect.target == "self"
        assert effect.status_effect_type == "damage_reduction"
        assert effect.status_value == 0.4


class TestAbilityAvailability:
    def test_is_available_when_off_cooldown(self):
        ability = Ability(
            name="Nuke", type="ultimate", cooldown=8, cooldown_remaining=0
        )
        assert ability.is_available

    def test_not_available_on_cooldown(self):
        ability = Ability(
            name="Nuke", type="ultimate", cooldown=8, cooldown_remaining=3
        )
        assert not ability.is_available


class TestFighter:
    def test_create_fighter(self):
        fighter = Fighter(
            id="striker",
            codename="Striker",
            hp=100,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert fighter.hp == 100
        assert fighter.is_alive

    def test_fighter_dead_at_zero_hp(self):
        fighter = Fighter(
            id="striker",
            codename="Striker",
            hp=0,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert not fighter.is_alive

    def test_hp_clamped_to_max(self):
        fighter = Fighter(
            id="striker",
            codename="Striker",
            hp=150,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert fighter.hp == 100

    def test_hp_clamped_to_zero(self):
        fighter = Fighter(
            id="striker",
            codename="Striker",
            hp=-10,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert fighter.hp == 0

    def test_energy_clamped_to_max(self):
        fighter = Fighter(
            id="striker",
            codename="Striker",
            hp=100,
            max_hp=100,
            energy=200,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert fighter.energy == 100

    def test_hp_percentage(self):
        fighter = Fighter(
            id="test",
            codename="Test",
            hp=30,
            max_hp=100,
            energy=50,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
        )
        assert fighter.hp_percentage == 0.3

    def test_get_ability_found(self):
        ability = Ability(name="Logic Missile", type="attack", damage=12)
        fighter = Fighter(
            id="test",
            codename="Test",
            hp=100,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[ability],
        )
        assert fighter.get_ability("Logic Missile") is not None
        assert fighter.get_ability("logic missile") is not None  # Case insensitive

    def test_get_ability_not_found(self):
        fighter = Fighter(
            id="test",
            codename="Test",
            hp=100,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
        )
        assert fighter.get_ability("Nonexistent") is None

    def test_has_status(self):
        fighter = Fighter(
            id="test",
            codename="Test",
            hp=100,
            max_hp=100,
            energy=100,
            max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[
                StatusEffect(name="Slowed", turns_remaining=2, effect_type="slow")
            ],
        )
        assert fighter.has_status("slow")
        assert not fighter.has_status("stun")


class TestArena:
    def test_valid_position(self):
        arena = Arena(width=8, height=6)
        assert arena.is_valid_position(Position(x=0, y=0))
        assert arena.is_valid_position(Position(x=7, y=5))
        assert not arena.is_valid_position(Position(x=8, y=0))
        assert not arena.is_valid_position(Position(x=-1, y=0))
        assert not arena.is_valid_position(Position(x=0, y=6))

    def test_get_hazard_at(self):
        hazard = Hazard(
            type="firewall", position=Position(x=3, y=3), damage=8, turns_remaining=3
        )
        arena = Arena(width=8, height=6, hazards=[hazard])
        assert arena.get_hazard_at(Position(x=3, y=3)) is not None
        assert arena.get_hazard_at(Position(x=0, y=0)) is None


class TestBattleState:
    def test_create_battle_state(self, striker_fighter, guardian_fighter, basic_arena):
        state = BattleState(
            match_id="test-001",
            turn=1,
            phase=MatchPhase.FIGHTING,
            fighters=[striker_fighter, guardian_fighter],
            arena=basic_arena,
        )
        assert state.turn == 1
        assert len(state.fighters) == 2

    def test_get_fighter(self, sample_battle_state):
        fighter = sample_battle_state.get_fighter("striker")
        assert fighter is not None
        assert fighter.codename == "Striker"

    def test_get_fighter_not_found(self, sample_battle_state):
        assert sample_battle_state.get_fighter("nonexistent") is None

    def test_get_opponent(self, sample_battle_state):
        opponent = sample_battle_state.get_opponent("striker")
        assert opponent is not None
        assert opponent.id == "guardian"

    def test_to_fighter_perspective(self, sample_battle_state):
        perspective = sample_battle_state.to_fighter_perspective("striker")
        assert perspective["turn"] == 1
        assert perspective["you"]["id"] == "striker"
        assert perspective["opponent"]["id"] == "guardian"
        assert "rules_reminder" in perspective
        assert "arena" in perspective

    def test_to_fighter_perspective_unknown_raises(self, sample_battle_state):
        with pytest.raises(ValueError):
            sample_battle_state.to_fighter_perspective("nonexistent")


class TestActionResponse:
    def test_valid_attack_response(self):
        resp = ActionResponse(
            turn=5,
            action={"type": "attack", "ability": "Quick Strike", "target": "guardian"},
            move={"direction": "left"},
            inner_monologue="Going in for the kill.",
            trash_talk="GG no re.",
        )
        assert resp.turn == 5
        assert resp.action["type"] == "attack"

    def test_defend_action(self):
        resp = ActionResponse(
            turn=5,
            action={"type": "defend"},
            move=None,
            inner_monologue="Playing it safe.",
            trash_talk="Come at me.",
        )
        assert resp.action["type"] == "defend"

    def test_wait_action(self):
        resp = ActionResponse(
            turn=3,
            action={"type": "wait"},
            inner_monologue="Conserving energy.",
            trash_talk="Patience is a virtue.",
        )
        assert resp.action["type"] == "wait"
        assert resp.move is None


class TestDirectionVectors:
    def test_all_directions_defined(self):
        assert len(DIRECTION_VECTORS) == 8

    def test_up_vector(self):
        assert DIRECTION_VECTORS[MoveDirection.UP] == (0, -1)

    def test_diagonal_vector(self):
        assert DIRECTION_VECTORS[MoveDirection.DOWN_RIGHT] == (1, 1)


class TestMatchPhase:
    def test_phase_values(self):
        assert MatchPhase.INIT == "init"
        assert MatchPhase.FIGHTING == "fighting"
        assert MatchPhase.RESOLVED == "resolved"

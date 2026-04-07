"""Shared test fixtures for LLM Smash Bros."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from llm_smash.engine.state import (
    Ability,
    BattleState,
    Fighter,
    MatchPhase,
    Arena,
    Position,
)


@pytest.fixture
def basic_attack_ability() -> Ability:
    return Ability(
        name="Quick Strike",
        type="attack",
        damage=12,
        energy_cost=0,
        cooldown=0,
        cooldown_remaining=0,
        range=2,
    )


@pytest.fixture
def striker_fighter(basic_attack_ability) -> Fighter:
    return Fighter(
        id="striker",
        codename="Striker",
        hp=80,
        max_hp=80,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[basic_attack_ability],
        status_effects=[],
    )


@pytest.fixture
def guardian_fighter() -> Fighter:
    return Fighter(
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
            Ability(
                name="Earthshatter",
                type="ultimate",
                damage=25,
                energy_cost=70,
                cooldown=8,
                cooldown_remaining=0,
                range=4,
                description="Shatters the ground for 25 damage and stuns the target for 1 turn.",
            ),
        ],
        status_effects=[],
    )


@pytest.fixture
def basic_arena() -> Arena:
    return Arena(width=8, height=6, hazards=[])


@pytest.fixture
def sample_battle_state(striker_fighter, guardian_fighter, basic_arena) -> BattleState:
    return BattleState(
        match_id="test-match-001",
        turn=1,
        phase=MatchPhase.FIGHTING,
        fighters=[striker_fighter, guardian_fighter],
        arena=basic_arena,
    )

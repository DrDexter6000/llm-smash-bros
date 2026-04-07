"""Shared test fixtures for LLM Smash Bros."""

import pytest
from llm_smash.engine.state import (
    Position,
    Ability,
    Fighter,
    Hazard,
    Arena,
    BattleState,
    MatchPhase,
)


@pytest.fixture
def basic_attack_ability() -> Ability:
    return Ability(
        name="Logic Missile",
        type="attack",
        damage=12,
        energy_cost=0,
        cooldown=0,
        cooldown_remaining=0,
        range=4,
    )


@pytest.fixture
def oracle_fighter(basic_attack_ability) -> Fighter:
    return Fighter(
        id="gpt-4o",
        codename="The Oracle",
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[basic_attack_ability],
        status_effects=[],
    )


@pytest.fixture
def artisan_fighter() -> Fighter:
    return Fighter(
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
            ),
            Ability(
                name="Context Window Strike",
                type="ultimate",
                damage=40,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=3,
                description="Massive cognitive overload burst. Slows enemy for 2 turns.",
            ),
        ],
        status_effects=[],
    )


@pytest.fixture
def basic_arena() -> Arena:
    return Arena(width=8, height=6, hazards=[])


@pytest.fixture
def sample_battle_state(oracle_fighter, artisan_fighter, basic_arena) -> BattleState:
    return BattleState(
        match_id="test-match-001",
        turn=1,
        phase=MatchPhase.FIGHTING,
        fighters=[oracle_fighter, artisan_fighter],
        arena=basic_arena,
    )

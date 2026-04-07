"""Tests for the combat resolution engine."""

import pytest
from llm_smash.engine.combat import (
    CombatResolver,
    ENERGY_REGEN_PER_TURN,
    HAZARD_SPAWN_INTERVAL,
    SUDDEN_DEATH_TURN,
    SUDDEN_DEATH_SPAWN_INTERVAL,
)
from llm_smash.engine.state import (
    Ability,
    Arena,
    Fighter,
    Hazard,
    Position,
    StatusEffect,
)


@pytest.fixture
def resolver():
    return CombatResolver(seed=42)


@pytest.fixture
def basic_ability():
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
def attacker(basic_ability):
    return Fighter(
        id="gpt-4o",
        codename="The Oracle",
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=0, y=0),
        abilities=[basic_ability],
        status_effects=[],
    )


@pytest.fixture
def defender():
    return Fighter(
        id="claude",
        codename="The Artisan",
        hp=85,
        max_hp=85,
        energy=100,
        max_energy=100,
        position=Position(x=2, y=0),
        abilities=[],
        status_effects=[],
    )


class TestCalculateDamage:
    def test_basic_damage_in_range(self, resolver, attacker, defender, basic_ability):
        """Damage should be near base value with variance."""
        damages = [
            resolver.calculate_damage(
                attacker, defender, basic_ability, is_defending=False
            )
            for _ in range(100)
        ]
        # With 12 base, variance ±15%, crits 1.5x: expect range ~10-27
        assert all(d >= 1 for d in damages)
        avg = sum(damages) / len(damages)
        assert 10 <= avg <= 18  # Average should hover around base

    def test_distance_penalty_applied(
        self, resolver, attacker, defender, basic_ability
    ):
        """Damage should be reduced when target is beyond ability range."""
        defender.position = Position(x=6, y=0)  # Distance 6, range 4
        damages = [
            resolver.calculate_damage(
                attacker, defender, basic_ability, is_defending=False
            )
            for _ in range(50)
        ]
        avg = sum(damages) / len(damages)
        assert avg < 12  # Should be noticeably below base due to distance penalty

    def test_defend_reduces_damage(self, resolver, attacker, defender, basic_ability):
        """Defending should reduce incoming damage by 20%."""
        resolver_a = CombatResolver(seed=42)
        resolver_b = CombatResolver(seed=42)  # Same seed for same rolls
        normal = resolver_a.calculate_damage(
            attacker, defender, basic_ability, is_defending=False
        )
        defended = resolver_b.calculate_damage(
            attacker, defender, basic_ability, is_defending=True
        )
        assert defended < normal

    def test_zero_damage_ability(self, resolver, attacker, defender):
        """An ability with 0 base damage should deal 0."""
        zero_ability = Ability(name="Buff", type="buff", damage=0)
        dmg = resolver.calculate_damage(
            attacker, defender, zero_ability, is_defending=False
        )
        assert dmg == 0

    def test_minimum_one_damage(self, resolver, attacker, defender, basic_ability):
        """Damage should never go below 1 for a damage-dealing ability."""
        basic_ability.damage = 1
        defender.position = Position(x=99, y=99)  # Very far away
        damages = [
            resolver.calculate_damage(
                attacker, defender, basic_ability, is_defending=True
            )
            for _ in range(50)
        ]
        assert all(d >= 1 for d in damages)


class TestResolveMovement:
    def test_move_right(self, resolver, attacker):
        new_pos = resolver.resolve_movement(
            attacker, "right", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=1, y=0)

    def test_move_down(self, resolver, attacker):
        new_pos = resolver.resolve_movement(
            attacker, "down", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=0, y=1)

    def test_move_diagonal(self, resolver, attacker):
        new_pos = resolver.resolve_movement(
            attacker, "down-right", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=1, y=1)

    def test_clamped_at_left_boundary(self, resolver, attacker):
        attacker.position = Position(x=0, y=0)
        new_pos = resolver.resolve_movement(
            attacker, "left", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=0, y=0)

    def test_clamped_at_right_boundary(self, resolver, attacker):
        attacker.position = Position(x=7, y=0)
        new_pos = resolver.resolve_movement(
            attacker, "right", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=7, y=0)

    def test_clamped_at_top_boundary(self, resolver, attacker):
        attacker.position = Position(x=0, y=0)
        new_pos = resolver.resolve_movement(
            attacker, "up", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=0, y=0)

    def test_clamped_at_bottom_boundary(self, resolver, attacker):
        attacker.position = Position(x=0, y=5)
        new_pos = resolver.resolve_movement(
            attacker, "down", arena_width=8, arena_height=6
        )
        assert new_pos == Position(x=0, y=5)

    def test_null_direction_stays_put(self, resolver, attacker):
        new_pos = resolver.resolve_movement(
            attacker, None, arena_width=8, arena_height=6
        )
        assert new_pos == attacker.position

    def test_invalid_direction_stays_put(self, resolver, attacker):
        new_pos = resolver.resolve_movement(
            attacker, "teleport", arena_width=8, arena_height=6
        )
        assert new_pos == attacker.position


class TestEnergyRegen:
    def test_regen_adds_five(self, resolver, attacker):
        attacker.energy = 50
        resolver.apply_energy_regen(attacker)
        assert attacker.energy == 50 + ENERGY_REGEN_PER_TURN

    def test_regen_capped_at_max(self, resolver, attacker):
        attacker.energy = 98
        resolver.apply_energy_regen(attacker)
        assert attacker.energy == 100

    def test_wait_bonus(self, resolver, attacker):
        attacker.energy = 50
        resolver.apply_wait_bonus(attacker)
        assert attacker.energy == 55

    def test_wait_bonus_capped(self, resolver, attacker):
        attacker.energy = 97
        resolver.apply_wait_bonus(attacker)
        assert attacker.energy == 100


class TestCooldowns:
    def test_cooldown_ticks_down(self, resolver, attacker):
        attacker.abilities[0].cooldown_remaining = 3
        resolver.apply_ability_cooldowns(attacker)
        assert attacker.abilities[0].cooldown_remaining == 2

    def test_cooldown_stops_at_zero(self, resolver, attacker):
        attacker.abilities[0].cooldown_remaining = 0
        resolver.apply_ability_cooldowns(attacker)
        assert attacker.abilities[0].cooldown_remaining == 0


class TestHazards:
    def test_hazard_damage_applied(self, resolver, attacker):
        arena = Arena(
            width=8,
            height=6,
            hazards=[
                Hazard(
                    type="firewall",
                    position=Position(x=0, y=0),
                    damage=8,
                    turns_remaining=3,
                )
            ],
        )
        events = resolver.apply_hazard_damage(attacker, arena)
        assert attacker.hp == 92
        assert len(events) == 1
        assert events[0].type == "hazard"

    def test_no_hazard_at_position(self, resolver, attacker):
        arena = Arena(
            width=8,
            height=6,
            hazards=[
                Hazard(
                    type="firewall",
                    position=Position(x=5, y=5),
                    damage=8,
                    turns_remaining=3,
                )
            ],
        )
        events = resolver.apply_hazard_damage(attacker, arena)
        assert attacker.hp == 100
        assert len(events) == 0

    def test_energy_drain_hazard(self, resolver, attacker):
        arena = Arena(
            width=8,
            height=6,
            hazards=[
                Hazard(
                    type="memory_leak",
                    position=Position(x=0, y=0),
                    damage=0,
                    effect_type="energy_drain",
                    effect_value=10.0,
                    turns_remaining=4,
                )
            ],
        )
        events = resolver.apply_hazard_damage(attacker, arena)
        assert attacker.energy == 90
        assert len(events) == 1

    def test_tick_hazards_removes_expired(self, resolver):
        arena = Arena(
            width=8,
            height=6,
            hazards=[
                Hazard(
                    type="firewall",
                    position=Position(x=0, y=0),
                    damage=8,
                    turns_remaining=1,
                ),
                Hazard(
                    type="firewall",
                    position=Position(x=5, y=5),
                    damage=8,
                    turns_remaining=3,
                ),
            ],
        )
        resolver.tick_hazards(arena)
        assert len(arena.hazards) == 1
        assert arena.hazards[0].position == Position(x=5, y=5)

    def test_spawn_hazard(self, resolver):
        arena = Arena(width=8, height=6, hazards=[])
        hazard = resolver.spawn_hazard(arena, occupied_positions=[])
        assert hazard is not None
        assert arena.is_valid_position(hazard.position)
        assert len(arena.hazards) == 1

    def test_spawn_avoids_occupied(self, resolver):
        """Hazard should not spawn on occupied positions."""
        arena = Arena(width=2, height=1, hazards=[])
        # Occupy (0,0)
        occupied = [Position(x=0, y=0)]
        hazard = resolver.spawn_hazard(arena, occupied_positions=occupied)
        if hazard is not None:
            assert hazard.position != Position(x=0, y=0)


class TestStatusEffects:
    def test_tick_status_removes_expired(self, resolver, attacker):
        attacker.status_effects = [
            StatusEffect(name="Slowed", turns_remaining=1, effect_type="slow"),
            StatusEffect(
                name="Boosted", turns_remaining=3, effect_type="damage_boost", value=0.3
            ),
        ]
        resolver.tick_status_effects(attacker)
        assert len(attacker.status_effects) == 1
        assert attacker.status_effects[0].name == "Boosted"


class TestHazardSpawnTiming:
    def test_spawns_every_five_turns(self, resolver):
        assert not resolver.should_spawn_hazard(1)
        assert not resolver.should_spawn_hazard(4)
        assert resolver.should_spawn_hazard(5)
        assert resolver.should_spawn_hazard(10)
        assert not resolver.should_spawn_hazard(11)

    def test_sudden_death_doubles_rate(self, resolver):
        assert resolver.should_spawn_hazard(40)
        assert not resolver.should_spawn_hazard(41)
        assert resolver.should_spawn_hazard(42)
        assert not resolver.should_spawn_hazard(43)
        assert resolver.should_spawn_hazard(44)

    def test_turn_zero_no_spawn(self, resolver):
        assert not resolver.should_spawn_hazard(0)

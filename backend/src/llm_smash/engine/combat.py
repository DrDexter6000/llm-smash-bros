"""Combat resolution engine for LLM Smash Bros.

Handles damage calculation, movement resolution, energy management,
hazard effects, and status effect processing. Uses seeded randomness
for deterministic testing.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from llm_smash.engine.state import (
    Ability,
    Arena,
    Fighter,
    Hazard,
    MoveDirection,
    Position,
    StatusEffect,
    TerrainType,
    TurnEvent,
    DIRECTION_VECTORS,
)

if TYPE_CHECKING:
    pass

# Constants from PRD Section 3.5
DAMAGE_VARIANCE = 0.15
CRITICAL_HIT_CHANCE = 0.20
CRITICAL_HIT_MULTIPLIER = 1.5
DISTANCE_PENALTY_MULTIPLIER = 0.5
DEFEND_REDUCTION = 0.80  # Defender takes 80% damage (20% reduction)
ENERGY_REGEN_PER_TURN = 5
WAIT_BONUS_ENERGY = 5
HAZARD_SPAWN_INTERVAL = 5
SUDDEN_DEATH_TURN = 40
SUDDEN_DEATH_SPAWN_INTERVAL = 2

HAZARD_TYPES: list[dict] = [
    {
        "type": "firewall",
        "damage": 8,
        "effect_type": "",
        "effect_value": 0.0,
        "turns": 3,
    },
    {
        "type": "memory_leak",
        "damage": 0,
        "effect_type": "energy_drain",
        "effect_value": 10.0,
        "turns": 4,
    },
]


class CombatResolver:
    """Resolves combat actions with deterministic randomness for testing."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def calculate_damage(
        self,
        attacker: Fighter,
        defender: Fighter,
        ability: Ability,
        is_defending: bool,
        arena: Arena | None = None,
    ) -> int:
        """Calculate damage dealt by an ability, accounting for variance, crits, distance, and defend."""
        if ability.damage <= 0:
            return 0

        base = ability.damage
        damage_boost = self._get_status_value(attacker, "damage_boost")
        if damage_boost > 0:
            base *= 1 + damage_boost

        # Variance: ±15%
        variance = self._rng.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
        damage = base * (1 + variance)

        # Critical hit: 20% chance → 1.5x
        if self._rng.random() < CRITICAL_HIT_CHANCE:
            damage *= CRITICAL_HIT_MULTIPLIER

        # Distance penalty: if target is out of ability range → 50% damage
        distance = attacker.position.distance_to(defender.position)
        effective_range = ability.range
        if (
            arena is not None
            and arena.get_terrain_at(attacker.position) == TerrainType.HIGH_GROUND
        ):
            effective_range += 1
        if distance > effective_range:
            damage *= DISTANCE_PENALTY_MULTIPLIER

        # Defend bonus: defender takes 80% damage
        if is_defending:
            damage *= DEFEND_REDUCTION

        if (
            arena is not None
            and ability.range > 2
            and arena.get_terrain_at(defender.position) == TerrainType.COVER
        ):
            damage *= 0.7

        damage_reduction = self._get_status_value(defender, "damage_reduction")
        if damage_reduction > 0:
            damage *= 1 - damage_reduction

        return max(1, int(damage))  # Minimum 1 damage

    def apply_status_effect(self, fighter: Fighter, status: StatusEffect) -> None:
        """Apply or refresh a status effect on a fighter."""
        fighter.status_effects = [
            effect
            for effect in fighter.status_effects
            if effect.effect_type != status.effect_type
        ]
        fighter.status_effects.append(status)

    def resolve_movement(
        self,
        fighter: Fighter,
        direction: str | None,
        arena: Arena | None = None,
    ) -> Position:
        """Resolve a movement command, clamping to arena bounds."""
        if direction is None:
            return fighter.position

        try:
            move_dir = MoveDirection(direction)
        except ValueError:
            return fighter.position

        arena_width = arena.width if arena is not None else 8
        arena_height = arena.height if arena is not None else 6

        dx, dy = DIRECTION_VECTORS[move_dir]
        new_x = max(0, min(fighter.position.x + dx, arena_width - 1))
        new_y = max(0, min(fighter.position.y + dy, arena_height - 1))
        new_position = Position(x=new_x, y=new_y)

        if arena is not None and not arena.is_passable(new_position):
            return fighter.position

        return new_position

    def apply_energy_regen(self, fighter: Fighter) -> None:
        """Apply passive energy regeneration (+5 per turn)."""
        new_energy = min(fighter.energy + ENERGY_REGEN_PER_TURN, fighter.max_energy)
        fighter.energy = new_energy

    def apply_wait_bonus(self, fighter: Fighter) -> None:
        """Apply bonus energy for choosing to wait (+5 extra)."""
        new_energy = min(fighter.energy + WAIT_BONUS_ENERGY, fighter.max_energy)
        fighter.energy = new_energy

    def apply_ability_cooldowns(self, fighter: Fighter) -> None:
        """Tick down all ability cooldowns by 1."""
        for ability in fighter.abilities:
            if ability.cooldown_remaining > 0:
                ability.cooldown_remaining -= 1

    def apply_hazard_damage(self, fighter: Fighter, arena: Arena) -> list[TurnEvent]:
        """Apply damage/effects from hazards at the fighter's position."""
        events: list[TurnEvent] = []
        hazard = arena.get_hazard_at(fighter.position)
        if hazard is None:
            return events

        if hazard.damage > 0:
            fighter.hp = max(0, fighter.hp - hazard.damage)
            events.append(
                TurnEvent(
                    type="hazard",
                    target_id=fighter.id,
                    value=hazard.damage,
                    description=f"{fighter.codename} takes {hazard.damage} damage from {hazard.type}!",
                )
            )

        if hazard.effect_type == "energy_drain":
            drain = int(hazard.effect_value)
            fighter.energy = max(0, fighter.energy - drain)
            events.append(
                TurnEvent(
                    type="hazard",
                    target_id=fighter.id,
                    value=drain,
                    description=f"{fighter.codename} loses {drain} energy from {hazard.type}!",
                )
            )

        return events

    def tick_hazards(self, arena: Arena) -> None:
        """Tick down hazard durations and remove expired ones."""
        remaining: list[Hazard] = []
        for hazard in arena.hazards:
            hazard.turns_remaining -= 1
            if hazard.turns_remaining > 0:
                remaining.append(hazard)
        arena.hazards = remaining

    def tick_status_effects(
        self, fighter: Fighter, active_effect_ids: set[int] | None = None
    ) -> None:
        """Tick down status effect durations and remove expired ones."""
        remaining: list[StatusEffect] = []
        for effect in fighter.status_effects:
            if active_effect_ids is not None and id(effect) not in active_effect_ids:
                remaining.append(effect)
                continue
            effect.turns_remaining -= 1
            if effect.turns_remaining > 0:
                remaining.append(effect)
        fighter.status_effects = remaining

    def _get_status_value(self, fighter: Fighter, effect_type: str) -> float:
        for effect in fighter.status_effects:
            if effect.effect_type == effect_type:
                return effect.value
        return 0.0

    def spawn_hazard(
        self, arena: Arena, occupied_positions: list[Position]
    ) -> Hazard | None:
        """Spawn a random hazard on an unoccupied tile."""
        hazard_template = self._rng.choice(HAZARD_TYPES)

        # Find a free position
        attempts = 0
        while attempts < 20:
            x = self._rng.randint(0, arena.width - 1)
            y = self._rng.randint(0, arena.height - 1)
            pos = Position(x=x, y=y)

            # Check not occupied by fighter or existing hazard
            if (
                pos not in occupied_positions
                and arena.get_hazard_at(pos) is None
                and arena.is_passable(pos)
            ):
                hazard = Hazard(
                    type=hazard_template["type"],
                    position=pos,
                    damage=hazard_template["damage"],
                    effect_type=hazard_template["effect_type"],
                    effect_value=hazard_template["effect_value"],
                    turns_remaining=hazard_template["turns"],
                )
                arena.hazards.append(hazard)
                return hazard
            attempts += 1

        return None

    def should_spawn_hazard(self, turn: int) -> bool:
        """Check if a hazard should spawn this turn (every 5 turns, doubled after turn 40)."""
        if turn < 1:
            return False
        interval = (
            SUDDEN_DEATH_SPAWN_INTERVAL
            if turn >= SUDDEN_DEATH_TURN
            else HAZARD_SPAWN_INTERVAL
        )
        return turn % interval == 0

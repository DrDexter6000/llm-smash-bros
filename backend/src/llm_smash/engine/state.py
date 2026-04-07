"""Core state models for LLM Smash Bros game engine.

All game state is represented as Pydantic models for type safety,
serialization, and JSON schema generation for LLM communication.
"""

from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class MatchPhase(str, Enum):
    """Match lifecycle phases."""

    INIT = "init"
    READY = "ready"
    FIGHTING = "fighting"
    RESOLVED = "resolved"


class ActionType(str, Enum):
    """Types of actions a fighter can take per turn."""

    ATTACK = "attack"
    DEFEND = "defend"
    WAIT = "wait"


class MoveDirection(str, Enum):
    """8-directional movement on the grid."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP_LEFT = "up-left"
    UP_RIGHT = "up-right"
    DOWN_LEFT = "down-left"
    DOWN_RIGHT = "down-right"


# Direction vectors for grid movement
DIRECTION_VECTORS: dict[MoveDirection, tuple[int, int]] = {
    MoveDirection.UP: (0, -1),
    MoveDirection.DOWN: (0, 1),
    MoveDirection.LEFT: (-1, 0),
    MoveDirection.RIGHT: (1, 0),
    MoveDirection.UP_LEFT: (-1, -1),
    MoveDirection.UP_RIGHT: (1, -1),
    MoveDirection.DOWN_LEFT: (-1, 1),
    MoveDirection.DOWN_RIGHT: (1, 1),
}


class Position(BaseModel):
    """A position on the arena grid."""

    x: int
    y: int

    def distance_to(self, other: Position) -> float:
        """Euclidean distance to another position."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def chebyshev_distance(self, other: Position) -> int:
        """Chebyshev (chess king) distance — max of dx, dy. Used for grid movement."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


class Ability(BaseModel):
    """A combat ability belonging to a fighter."""

    name: str
    type: str  # "attack", "ultimate", "buff", "trap"
    damage: int = 0
    energy_cost: int = 0
    cooldown: int = 0  # Total cooldown turns after use
    cooldown_remaining: int = 0  # Current cooldown counter
    range: int = 1
    description: str = ""
    effects: list[AbilityEffect] = Field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Whether this ability can be used right now."""
        return self.cooldown_remaining == 0


class StatusEffect(BaseModel):
    """A temporary status effect on a fighter."""

    name: str
    turns_remaining: int
    effect_type: str  # "slow", "stun", "damage_boost", "damage_reduction", "confused"
    value: float = 0.0  # Magnitude of the effect


class AbilityEffect(BaseModel):
    """A non-damage effect attached to an ability."""

    type: str  # "status_apply", "self_damage", "knockback"
    target: str  # "self", "opponent"
    status_name: str = ""
    status_effect_type: str = ""
    status_value: float = 0.0
    status_duration: int = 0
    knockback_distance: int = 0
    self_damage: int = 0


class Fighter(BaseModel):
    """A fighter in the arena with all combat stats."""

    id: str
    codename: str
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    position: Position
    abilities: list[Ability]
    status_effects: list[StatusEffect] = Field(default_factory=list)
    last_action: dict[str, Any] | None = None

    @model_validator(mode="after")
    def clamp_values(self) -> "Fighter":
        """Clamp HP and energy to valid ranges [0, max]."""
        object.__setattr__(self, "hp", max(0, min(self.hp, self.max_hp)))
        object.__setattr__(self, "energy", max(0, min(self.energy, self.max_energy)))
        return self

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def hp_percentage(self) -> float:
        if self.max_hp == 0:
            return 0.0
        return self.hp / self.max_hp

    def get_ability(self, name: str) -> Ability | None:
        """Look up an ability by name (case-insensitive)."""
        for ability in self.abilities:
            if ability.name.lower() == name.lower():
                return ability
        return None

    def has_status(self, effect_type: str) -> bool:
        """Check if fighter has an active status effect of the given type."""
        return any(se.effect_type == effect_type for se in self.status_effects)


class Hazard(BaseModel):
    """An arena hazard occupying a tile."""

    type: str  # "firewall", "memory_leak", "hallucination_zone", "token_overflow"
    position: Position
    damage: int = 0
    effect_type: str = ""  # For non-damage hazards
    effect_value: float = 0.0
    turns_remaining: int = 1


class Arena(BaseModel):
    """The battle arena grid."""

    width: int = 8
    height: int = 6
    hazards: list[Hazard] = Field(default_factory=list)

    def is_valid_position(self, pos: Position) -> bool:
        """Check if a position is within the arena bounds."""
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get_hazard_at(self, pos: Position) -> Hazard | None:
        """Get hazard at a specific position, if any."""
        for hazard in self.hazards:
            if hazard.position == pos:
                return hazard
        return None


class BattleState(BaseModel):
    """Complete state of a match at a given turn."""

    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    turn: int = 1
    phase: MatchPhase = MatchPhase.INIT
    fighters: list[Fighter]
    arena: Arena
    audience_events: list[dict[str, Any]] = Field(default_factory=list)

    def get_fighter(self, fighter_id: str) -> Fighter | None:
        """Look up a fighter by ID."""
        for fighter in self.fighters:
            if fighter.id == fighter_id:
                return fighter
        return None

    def get_opponent(self, fighter_id: str) -> Fighter | None:
        """Get the opponent of a given fighter (assumes 2-player match)."""
        for fighter in self.fighters:
            if fighter.id != fighter_id:
                return fighter
        return None

    def to_fighter_perspective(self, fighter_id: str) -> dict[str, Any]:
        """Generate the battle state JSON from one fighter's perspective.

        This is what gets sent to the LLM API — the fighter sees itself as 'you'
        and the opponent as 'opponent'.
        """
        me = self.get_fighter(fighter_id)
        opponent = self.get_opponent(fighter_id)
        if me is None or opponent is None:
            raise ValueError(f"Fighter '{fighter_id}' not found in battle state")

        return {
            "turn": self.turn,
            "you": {
                "id": me.id,
                "codename": me.codename,
                "hp": me.hp,
                "max_hp": me.max_hp,
                "position": {"x": me.position.x, "y": me.position.y},
                "energy": me.energy,
                "max_energy": me.max_energy,
                "abilities": [
                    {
                        "name": a.name,
                        "type": a.type,
                        "damage": a.damage,
                        "energy_cost": a.energy_cost,
                        "cooldown_remaining": a.cooldown_remaining,
                        "range": a.range,
                        "description": a.description,
                    }
                    for a in me.abilities
                ],
                "status_effects": [se.name for se in me.status_effects],
                "last_action": me.last_action,
            },
            "opponent": {
                "id": opponent.id,
                "codename": opponent.codename,
                "hp": opponent.hp,
                "max_hp": opponent.max_hp,
                "position": {"x": opponent.position.x, "y": opponent.position.y},
                "energy": opponent.energy,
                "status_effects": [se.name for se in opponent.status_effects],
                "last_action": opponent.last_action,
            },
            "arena": {
                "width": self.arena.width,
                "height": self.arena.height,
                "hazards": [
                    {
                        "type": h.type,
                        "position": {"x": h.position.x, "y": h.position.y},
                        "damage": h.damage,
                        "turns_remaining": h.turns_remaining,
                    }
                    for h in self.arena.hazards
                ],
            },
            "audience_events": self.audience_events,
            "rules_reminder": (
                "Respond with valid JSON. You may move 1 tile AND perform 1 action "
                "(attack, ability, or defend) per turn. Movement resolves first, then action. "
                "You MUST include inner_monologue and trash_talk fields."
            ),
        }


class ActionResponse(BaseModel):
    """Parsed and validated action response from an LLM."""

    turn: int
    action: dict[
        str, Any
    ]  # {"type": "attack|defend|wait", "ability": "...", "target": "..."}
    move: dict[str, Any] | None = None  # {"direction": "left"} or None
    inner_monologue: str = ""
    trash_talk: str = ""


class TurnEvent(BaseModel):
    """A single event that occurred during a turn (for logging/display)."""

    type: str  # "damage", "move", "ability_used", "fumble", "hazard", "ko", "status_applied"
    source_id: str = ""
    target_id: str = ""
    value: int = 0
    description: str = ""


class TurnLog(BaseModel):
    """Complete log of a single turn."""

    turn_number: int
    actions: dict[str, ActionResponse | None] = Field(
        default_factory=dict
    )  # fighter_id -> response
    events: list[TurnEvent] = Field(default_factory=list)
    state_after: dict[str, Any] | None = None  # Serialized BattleState after resolution
    fumbles: list[str] = Field(default_factory=list)  # fighter_ids that fumbled


class MatchResult(BaseModel):
    """Final result of a completed match."""

    match_id: str
    winner: str | None = None  # fighter_id or None for draw
    is_draw: bool = False
    total_turns: int = 0
    total_fumbles: int = 0
    turn_log: list[TurnLog] = Field(default_factory=list)
    end_reason: str = ""  # "ko", "timeout", "draw", "mutual_fumble"

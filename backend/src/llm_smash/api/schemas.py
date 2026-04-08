"""Pydantic schemas for the FastAPI API layer."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MatchCreateRequest(BaseModel):
    fighter1_archetype: str
    fighter2_archetype: str
    fighter1_model: str | None = None
    fighter2_model: str | None = None
    max_turns: int = Field(default=50, ge=1)
    seed: int | None = None
    timeout: float = Field(default=8.0, gt=0)


class MatchCreateResponse(BaseModel):
    match_id: str


class MatchFighterInfo(BaseModel):
    slot_id: str
    archetype_id: str
    codename: str
    model: str | None = None


class MatchSummary(BaseModel):
    match_id: str
    status: Literal["running", "completed", "error"]
    fighters: list[MatchFighterInfo]
    winner: str | None = None
    turn_count: int = 0
    created_at: float
    is_draw: bool = False
    end_reason: str | None = None
    total_fumbles: int = 0
    error: str | None = None


class MatchTurnsResponse(BaseModel):
    match_id: str
    status: Literal["running", "completed", "error"]
    turns: list[dict[str, Any]]


class ArchetypeAbilityInfo(BaseModel):
    name: str
    type: str
    damage: int
    energy_cost: int
    cooldown: int
    range: int
    description: str


class ArchetypeInfo(BaseModel):
    id: str
    codename: str
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    abilities: list[ArchetypeAbilityInfo]

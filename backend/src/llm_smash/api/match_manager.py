"""In-memory match lifecycle management for the API layer."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import HTTPException

from llm_smash.cli import serialize_match_result
from llm_smash.engine.game import GameEngine, MatchConfig
from llm_smash.engine.state import (
    Arena,
    BattleState,
    Fighter,
    MatchPhase,
    MatchResult,
    Position,
    TurnLog,
)
from llm_smash.engine.terrain import TerrainGenerator
from llm_smash.fighters.roster import ARCHETYPE_IDS, get_all_archetypes, get_fighter
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.mock_client import MockLLMClient

from .schemas import (
    ArchetypeInfo,
    MatchCreateRequest,
    MatchFighterInfo,
    MatchSummary,
    MatchTurnsResponse,
)
from .ws import ConnectionManager


MatchStatus = Literal["running", "completed", "error"]


@dataclass(slots=True)
class MatchRecord:
    match_id: str
    status: MatchStatus
    fighters: list[MatchFighterInfo]
    config: MatchCreateRequest
    created_at: float
    turns_so_far: list[TurnLog] = field(default_factory=list)
    current_state: dict[str, Any] | None = None
    start_message: dict[str, Any] | None = None
    start_message_sent: bool = False
    result: MatchResult | None = None
    error: str | None = None
    task: asyncio.Task[None] | None = None

    def to_summary(self) -> MatchSummary:
        return MatchSummary(
            match_id=self.match_id,
            status=self.status,
            fighters=self.fighters,
            winner=self.result.winner if self.result else None,
            turn_count=self.result.total_turns
            if self.result
            else len(self.turns_so_far),
            created_at=self.created_at,
            is_draw=self.result.is_draw if self.result else False,
            end_reason=self.result.end_reason if self.result else None,
            total_fumbles=self.result.total_fumbles if self.result else 0,
            error=self.error,
        )

    def to_turns_response(self) -> MatchTurnsResponse:
        turns = self.result.turn_log if self.result else self.turns_so_far
        return MatchTurnsResponse(
            match_id=self.match_id,
            status=self.status,
            turns=[turn.model_dump(mode="json") for turn in turns],
        )

    def to_replay(self) -> dict:
        if self.result is None:
            raise HTTPException(
                status_code=409, detail="Match replay is not available yet"
            )
        return serialize_match_result(self.result)


class MatchManager:
    """In-memory match storage and background execution."""

    def __init__(self) -> None:
        self._matches: dict[str, MatchRecord] = {}
        self.ws_manager = ConnectionManager()
        self._mock_client_latency_ms = 50.0

    async def create_match(self, request: MatchCreateRequest) -> str:
        self._validate_request(request)

        match_id = uuid.uuid4().hex[:8]
        fighters = self._build_fighter_infos(request)
        record = MatchRecord(
            match_id=match_id,
            status="running",
            fighters=fighters,
            config=request,
            created_at=time.time(),
        )
        self._matches[match_id] = record
        record.task = asyncio.create_task(
            self._run_match(match_id), name=f"match-{match_id}"
        )
        return match_id

    def get_match(self, match_id: str) -> MatchRecord | None:
        return self._matches.get(match_id)

    def list_matches(self, limit: int = 20) -> list[MatchSummary]:
        records = sorted(
            self._matches.values(),
            key=lambda record: record.created_at,
            reverse=True,
        )
        return [record.to_summary() for record in records[:limit]]

    def list_archetypes(self) -> list[ArchetypeInfo]:
        return [
            ArchetypeInfo(
                id=archetype.id,
                codename=archetype.codename,
                hp=archetype.hp,
                max_hp=archetype.max_hp,
                energy=archetype.energy,
                max_energy=archetype.max_energy,
                abilities=[
                    {
                        "name": ability.name,
                        "type": ability.type,
                        "damage": ability.damage,
                        "energy_cost": ability.energy_cost,
                        "cooldown": ability.cooldown,
                        "range": ability.range,
                        "description": ability.description,
                    }
                    for ability in archetype.abilities
                ],
            )
            for archetype in get_all_archetypes()
        ]

    async def _run_match(self, match_id: str) -> None:
        record = self._matches[match_id]
        slot_ids = [fighter.slot_id for fighter in record.fighters]
        archetype_ids = [fighter.archetype_id for fighter in record.fighters]

        async def on_turn(turn_log: TurnLog) -> None:
            record.turns_so_far.append(turn_log)
            record.current_state = turn_log.state_after
            await self.ws_manager.broadcast(
                match_id,
                {
                    "type": "turn",
                    "turn_number": turn_log.turn_number,
                    "turn_log": turn_log.model_dump(mode="json"),
                },
            )

        config = MatchConfig(
            fighter_ids=slot_ids,
            max_turns=record.config.max_turns,
            timeout_per_turn=record.config.timeout,
            seed=record.config.seed,
        )
        llm_clients: dict[str, LLMAdapter] = {
            slot_id: MockLLMClient(
                fighter_id=slot_id,
                latency_ms=self._mock_client_latency_ms,
                seed=(record.config.seed or 0) + index,
            )
            for index, slot_id in enumerate(slot_ids, start=1)
        }

        engine = GameEngine(
            config=config, llm_clients=llm_clients, event_callback=on_turn
        )
        engine.state = self._build_initial_state(
            match_id=record.match_id,
            slot_ids=slot_ids,
            archetype_ids=archetype_ids,
            seed=record.config.seed,
        )
        record.current_state = engine.state.model_dump(mode="json")
        record.start_message = {
            "type": "match_start",
            "match_id": match_id,
            "fighters": [
                fighter.model_dump(mode="json") for fighter in record.fighters
            ],
            "arena": engine.state.arena.model_dump(mode="json"),
        }

        try:
            await self.ws_manager.broadcast(match_id, record.start_message)
            record.start_message_sent = True
            record.result = await engine.run_match()
            record.status = "completed"
            record.current_state = engine.state.model_dump(mode="json")
            await self.ws_manager.broadcast(
                match_id,
                {
                    "type": "match_end",
                    "result": record.result.model_dump(mode="json"),
                },
            )
        except Exception as exc:
            record.status = "error"
            record.error = str(exc)
            await self.ws_manager.broadcast(
                match_id,
                {"type": "error", "message": str(exc)},
            )
        finally:
            await self.ws_manager.cleanup(match_id)

    def _validate_request(self, request: MatchCreateRequest) -> None:
        invalid = [
            archetype_id
            for archetype_id in [request.fighter1_archetype, request.fighter2_archetype]
            if archetype_id not in ARCHETYPE_IDS
        ]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown archetype(s): {', '.join(invalid)}",
            )

    def _build_fighter_infos(
        self, request: MatchCreateRequest
    ) -> list[MatchFighterInfo]:
        archetype_ids = [request.fighter1_archetype, request.fighter2_archetype]
        model_names = [request.fighter1_model, request.fighter2_model]
        is_mirror = archetype_ids[0] == archetype_ids[1]
        fighter_infos: list[MatchFighterInfo] = []

        for index, (slot_id, archetype_id, model_name) in enumerate(
            zip(["fighter_a", "fighter_b"], archetype_ids, model_names, strict=True)
        ):
            fighter = get_fighter(archetype_id)
            codename = fighter.codename
            if is_mirror:
                codename = f"{codename} {'A' if index == 0 else 'B'}"
            fighter_infos.append(
                MatchFighterInfo(
                    slot_id=slot_id,
                    archetype_id=archetype_id,
                    codename=codename,
                    model=model_name,
                )
            )

        return fighter_infos

    def _build_initial_state(
        self,
        match_id: str,
        slot_ids: list[str],
        archetype_ids: list[str],
        seed: int | None,
    ) -> BattleState:
        fighters: list[Fighter] = []
        is_mirror = archetype_ids[0] == archetype_ids[1]

        for index, (slot_id, archetype_id) in enumerate(
            zip(slot_ids, archetype_ids, strict=True)
        ):
            fighter = get_fighter(archetype_id)
            fighter.id = slot_id
            if is_mirror:
                fighter.codename = f"{fighter.codename} {'A' if index == 0 else 'B'}"
            fighters.append(fighter)

        fighters[0].position = Position(x=1, y=3)
        fighters[1].position = Position(x=6, y=3)

        arena = Arena()
        TerrainGenerator(seed=seed).generate(
            arena,
            start_positions=[fighter.position for fighter in fighters],
        )

        return BattleState(
            match_id=match_id,
            fighters=fighters,
            arena=arena,
            phase=MatchPhase.READY,
        )

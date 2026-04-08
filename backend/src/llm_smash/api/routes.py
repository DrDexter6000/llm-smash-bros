"""FastAPI routes for match lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from .match_manager import MatchManager
from .schemas import (
    MatchCreateRequest,
    MatchCreateResponse,
    MatchSummary,
    MatchTurnsResponse,
)

router = APIRouter()


def get_match_manager(request: Request) -> MatchManager:
    return request.app.state.match_manager


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/matches", response_model=MatchCreateResponse, status_code=201)
async def create_match(
    request: MatchCreateRequest,
    manager: MatchManager = Depends(get_match_manager),
) -> MatchCreateResponse:
    match_id = await manager.create_match(request)
    return MatchCreateResponse(match_id=match_id)


@router.get("/matches", response_model=list[MatchSummary])
async def list_matches(
    limit: int = 20,
    manager: MatchManager = Depends(get_match_manager),
) -> list[MatchSummary]:
    return manager.list_matches(limit=limit)


@router.get("/matches/{match_id}", response_model=MatchSummary)
async def get_match(
    match_id: str,
    manager: MatchManager = Depends(get_match_manager),
) -> MatchSummary:
    match = manager.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match.to_summary()


@router.get("/matches/{match_id}/turns", response_model=MatchTurnsResponse)
async def get_match_turns(
    match_id: str,
    manager: MatchManager = Depends(get_match_manager),
) -> MatchTurnsResponse:
    match = manager.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match.to_turns_response()


@router.get("/matches/{match_id}/replay")
async def get_match_replay(
    match_id: str,
    manager: MatchManager = Depends(get_match_manager),
) -> dict:
    match = manager.get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match.to_replay()


@router.get("/archetypes")
async def list_archetypes(
    manager: MatchManager = Depends(get_match_manager),
) -> list[dict]:
    return [
        archetype.model_dump(mode="json") for archetype in manager.list_archetypes()
    ]

"""FastAPI routes for match lifecycle endpoints."""

from __future__ import annotations

import asyncio

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)

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


@router.websocket("/matches/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str) -> None:
    manager: MatchManager = websocket.app.state.match_manager
    match = manager.get_match(match_id)

    if match is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Match not found"})
        await websocket.close(code=1008)
        return

    if match.status == "completed" and match.result is not None:
        await websocket.accept()
        await websocket.send_json(
            {"type": "match_end", "result": match.result.model_dump(mode="json")}
        )
        await websocket.close()
        return

    if match.status == "error":
        await websocket.accept()
        await websocket.send_json(
            {"type": "error", "message": match.error or "Match failed"}
        )
        await websocket.close(code=1011)
        return

    queue = await manager.ws_manager.connect(match_id, websocket)

    if match.turns_so_far and match.current_state is not None:
        await websocket.send_json(
            {
                "type": "state_sync",
                "turns_so_far": [
                    turn_log.model_dump(mode="json") for turn_log in match.turns_so_far
                ],
                "current_state": match.current_state,
            }
        )
    elif match.start_message_sent and match.start_message is not None:
        await websocket.send_json(match.start_message)

    try:
        while True:
            receive_task = asyncio.create_task(websocket.receive_json())
            queue_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                {receive_task, queue_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for pending_task in pending:
                pending_task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

            if queue_task in done:
                outbound_message = queue_task.result()
                if outbound_message is None:
                    await websocket.close()
                    break
                await websocket.send_json(outbound_message)
                continue

            message = receive_task.result()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.ws_manager.disconnect(match_id, websocket)
    finally:
        manager.ws_manager.disconnect(match_id, websocket)

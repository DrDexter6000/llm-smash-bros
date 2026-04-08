"""WebSocket connection management for live match spectators."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass(slots=True)
class ManagedConnection:
    websocket: WebSocket
    queue: asyncio.Queue[dict[str, Any] | None]


class ConnectionManager:
    """Manage spectator WebSocket connections grouped by match."""

    def __init__(self) -> None:
        self._connections: dict[str, list[ManagedConnection]] = defaultdict(list)

    async def connect(
        self, match_id: str, websocket: WebSocket
    ) -> asyncio.Queue[dict[str, Any] | None]:
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._connections[match_id].append(
            ManagedConnection(websocket=websocket, queue=queue)
        )
        return queue

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(match_id)
        if connections is None:
            return

        connection = next(
            (item for item in connections if item.websocket is websocket),
            None,
        )
        if connection is None:
            return

        connections.remove(connection)
        if not connections:
            self._connections.pop(match_id, None)

    async def broadcast(self, match_id: str, message: dict) -> None:
        for connection in list(self._connections.get(match_id, [])):
            await connection.queue.put(message)

    async def cleanup(self, match_id: str) -> None:
        connections = self._connections.pop(match_id, [])
        for connection in connections:
            await connection.queue.put(None)

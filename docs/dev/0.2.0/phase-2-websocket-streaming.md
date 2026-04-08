# Phase 2 — WebSocket Match Streaming

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 2`
**Prerequisites:** Phase 1 complete (FastAPI app, MatchManager, REST endpoints)

---

## §1 Phase Goal & Purpose

Add real-time WebSocket streaming so spectators can watch matches **as they happen**, turn by turn. This is the architectural difference between "check back later for results" and "watch it live" — the core spectator experience that makes this project worth putting on a screen.

**Why this matters:**
- REST polling is acceptable for match results, but it cannot deliver the drama of watching a fight unfold in real time.
- The CLI's `event_callback` pattern in `GameEngine` already supports per-turn hooks. WebSocket streaming is the natural web equivalent.
- Live streaming enables future features: live spectator chat, audience interaction, tournament brackets with live feeds.
- Per `STRATEGY §2.3`, strategy should be visible. Real-time turn delivery is the foundation of visibility in a browser.

---

## §2 Prerequisites & Dependencies

- Phase 1 complete: FastAPI app running, MatchManager creates and stores matches, REST endpoints work.
- Understanding of: `GameEngine.event_callback` (async callback per turn), `TurnLog` structure, FastAPI WebSocket support.
- Understanding of: WebSocket lifecycle (connect → receive messages → disconnect), JSON message framing.

---

## §3 Execution Rules

### MUST DO

- Add a WebSocket endpoint at `/api/matches/{match_id}/ws` that streams turn events in real time.
- Integrate with `GameEngine`'s existing `event_callback` to push `TurnLog` data to connected WebSocket clients.
- Support multiple spectators on the same match (broadcast pattern).
- Handle WebSocket lifecycle gracefully: client connects mid-match (receives current state + subsequent turns), client disconnects (no crash), match ends (send final result + close).
- Define a clear WebSocket message protocol (JSON messages with `type` field).
- Add a WebSocket endpoint for starting a match with live streaming: POST to create + WS to watch should work together.
- Write tests for WebSocket behavior using `httpx` or `starlette.testclient.TestClient`.
- All existing tests must continue to pass.

### MUST NOT DO

- Do not implement chat or audience interaction (v0.3.0).
- Do not add frontend code (Phase 3).
- Do not change the game engine or combat system.
- Do not add authentication to WebSocket connections.
- Do not persist WebSocket connection state to disk.
- Do not use third-party WebSocket libraries beyond what FastAPI provides.

---

## §4 Task Breakdown

### Task 2.1: Design WebSocket Message Protocol

Define the JSON message types sent from server to client:

```python
# Server → Client messages
{"type": "match_start", "match_id": "abc123", "fighters": [...], "arena": {...}}
{"type": "turn",        "turn_number": 5,  "turn_log": {...}}  # TurnLog serialized
{"type": "match_end",   "result": {...}}  # MatchResult serialized
{"type": "error",       "message": "Match not found"}
{"type": "state_sync",  "battle_state": {...}, "turns_so_far": [...]}  # For late joiners
```

Client → Server messages (minimal for v0.2.0):
```python
{"type": "ping"}  # keepalive
```

Document these in a `WS_PROTOCOL.md` or as docstrings in the WebSocket handler.

### Task 2.2: Implement ConnectionManager

Create `backend/src/llm_smash/api/ws.py`:

```python
class ConnectionManager:
    """Manages WebSocket connections per match."""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}  # match_id → [ws, ...]

    async def connect(self, match_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections.setdefault(match_id, []).append(websocket)

    async def disconnect(self, match_id: str, websocket: WebSocket):
        conns = self._connections.get(match_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, match_id: str, message: dict):
        """Send a message to all spectators of a match."""
        conns = self._connections.get(match_id, [])
        disconnected = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            conns.remove(ws)

    def cleanup(self, match_id: str):
        """Remove all connections for a finished match."""
        self._connections.pop(match_id, None)
```

### Task 2.3: Wire GameEngine Event Callback to WebSocket Broadcast

Modify `MatchManager` (from Phase 1) to pass a WebSocket-broadcasting `event_callback` to `GameEngine`:

```python
async def _run_match(self, match_id: str):
    async def ws_callback(turn_log: TurnLog):
        await self.ws_manager.broadcast(match_id, {
            "type": "turn",
            "turn_number": turn_log.turn_number,
            "turn_log": turn_log.model_dump(mode="json"),
        })

    engine = GameEngine(
        config=self._matches[match_id].config,
        llm_clients=clients,
        event_callback=ws_callback,
    )

    # Broadcast match_start
    await self.ws_manager.broadcast(match_id, {
        "type": "match_start",
        "match_id": match_id,
        "fighters": [...],
        "arena": {...},
    })

    result = await engine.run_match()

    # Broadcast match_end
    await self.ws_manager.broadcast(match_id, {
        "type": "match_end",
        "result": result.model_dump(mode="json"),
    })

    self.ws_manager.cleanup(match_id)
```

### Task 2.4: Implement WebSocket Endpoint

In `routes.py` or a new `ws_routes.py`:

```python
@router.websocket("/matches/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str):
    match = manager.get_match(match_id)
    if not match:
        await websocket.close(code=4004, reason="Match not found")
        return

    await manager.ws_manager.connect(match_id, websocket)

    # If match is already in progress, send state_sync
    if match.status == "running" and match.turns_so_far:
        await websocket.send_json({
            "type": "state_sync",
            "battle_state": match.current_state_snapshot(),
            "turns_so_far": [t.model_dump(mode="json") for t in match.turns_so_far],
        })

    # If match is already completed, send result immediately
    if match.status == "completed":
        await websocket.send_json({
            "type": "match_end",
            "result": match.result.model_dump(mode="json"),
        })

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.ws_manager.disconnect(match_id, websocket)
```

### Task 2.5: Expose Turn History During Match Execution

The current `MatchManager` only stores the final `MatchResult`. For late-joining spectators and state_sync, it needs to also store turns as they happen.

Extend `MatchRecord` to accumulate turns:

```python
class MatchRecord:
    match_id: str
    status: str
    config: MatchConfig
    turns_so_far: list[TurnLog] = []   # populated during match
    result: MatchResult | None = None  # populated after match
    current_state: BattleState | None = None  # updated each turn
```

The `event_callback` should append each `TurnLog` to `turns_so_far` AND update `current_state`.

### Task 2.6: Write WebSocket Tests

Create `backend/tests/test_websocket.py`:

```python
from starlette.testclient import TestClient
from llm_smash.api.app import create_app

def test_ws_match_stream():
    app = create_app()
    client = TestClient(app)

    # Create a match
    r = client.post("/api/matches", json={
        "fighter1_archetype": "striker",
        "fighter2_archetype": "guardian",
    })
    match_id = r.json()["match_id"]

    # Connect WebSocket
    with client.websocket_connect(f"/api/matches/{match_id}/ws") as ws:
        # Should receive match_start or state_sync
        msg = ws.receive_json()
        assert msg["type"] in ("match_start", "state_sync")

        # Collect turn messages until match_end
        turns = []
        while True:
            msg = ws.receive_json()
            if msg["type"] == "turn":
                turns.append(msg)
            elif msg["type"] == "match_end":
                break

        assert len(turns) > 0
        assert "result" in msg

def test_ws_match_not_found():
    app = create_app()
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/matches/nonexistent/ws") as ws:
            pass  # should be rejected

def test_ws_ping_pong():
    # Connect to a running match, send ping, expect pong
    ...

def test_ws_late_join():
    # Start a match, wait a bit, then connect — should receive state_sync
    ...
```

### Task 2.7: Final Verification

```bash
# All tests pass
cd backend && uv run pytest -q

# Manual WebSocket test with websocat or similar:
python -m llm_smash --serve &
# Create match via REST, then:
# websocat ws://localhost:8000/api/matches/{id}/ws
# Observe turn-by-turn JSON messages
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | WebSocket endpoint exists | No WS endpoint | `/api/matches/{id}/ws` accepts connections |
| 2 | Turn-by-turn streaming works | Client receives nothing during match | Client receives `turn` messages as the match progresses |
| 3 | Match start/end events sent | No lifecycle messages | Client receives `match_start` and `match_end` |
| 4 | Late join gets state sync | Late joiner sees nothing | Late joiner receives `state_sync` with current state and past turns |
| 5 | Multiple spectators supported | Only one connection per match | Multiple WS clients receive the same turn broadcasts |
| 6 | Disconnection is graceful | Server crashes on client disconnect | Disconnected clients are removed, match continues |
| 7 | REST endpoints still work | Phase 1 endpoints broken | All REST endpoints from Phase 1 still functional |
| 8 | WebSocket tests pass | No WS tests | All WS tests green |
| 9 | All existing tests pass | Any pre-existing test fails | All 189+ tests still pass |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Start a match, connect via WebSocket, watch turns arrive. Do they arrive in real time or only after match ends?
- [ ] Connect two browser tabs/websocat sessions to the same match. Do both receive the same turns?
- [ ] Disconnect one client mid-match. Does the match continue? Does the other client still receive turns?
- [ ] Connect to an already-completed match. Do you receive the result immediately?
- [ ] Read the WebSocket handler code. Is there a risk of memory leak (connections never cleaned up)?
- [ ] Run full test suite. All green?

---

## §7 Self-Optimization & Retry Guidance

**If WebSocket messages are not received during match:**
- Check that `event_callback` is actually being called by `GameEngine`. Add a print/log statement.
- Check that `broadcast` is not failing silently (catch and log exceptions).
- Check that the WebSocket receive loop isn't blocking (it should be — the turns come via broadcast from the match task, not from client messages).

**If late join doesn't work:**
- Verify that `turns_so_far` is being populated during match execution.
- Check timing: if the match finishes before the WS connection is established, the client should receive `match_end` instead of `state_sync`.

**If tests are flaky due to timing:**
- Use `asyncio.Event` or similar synchronization primitives in tests.
- Increase polling intervals in test assertions.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

---

## §9 Next Phase Pointer

**Next:** Phase 3 — Frontend Scaffold & Arena Renderer (`docs/dev/0.2.0/phase-3-frontend-scaffold.md`)

**What Phase 3 needs from this phase:**
- Working WebSocket endpoint that streams turn events in real time.
- Defined message protocol (message types and JSON shapes).
- REST endpoints for match creation, listing, and archetype info.

**What Phase 3 does NOT need from this phase:**
- Any frontend code.
- CORS configuration (Phase 3 adds it).
- Chat or audience features (v0.3.0).

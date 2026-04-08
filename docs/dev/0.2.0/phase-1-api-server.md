# Phase 1 — API Server Foundation

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 1`
**Prerequisites:** Phase 0 complete (CI, deps verified, retry logic)

---

## §1 Phase Goal & Purpose

Stand up a FastAPI server that can create matches, run them via the existing `GameEngine`, and serve results through REST endpoints. This phase turns the CLI-only engine into a **headless match service** that the frontend (Phase 3+) and WebSocket layer (Phase 2) will consume.

**Why this matters:**
- The game engine is currently only accessible via `python -m llm_smash`. There is no programmatic way to start a match, query its state, or retrieve results from another process.
- The web spectator layer needs an API to start matches, poll status, and fetch replays.
- Separating "match execution" from "match display" is the architectural pivot that enables the entire v0.2.0 vision.

---

## §2 Prerequisites & Dependencies

- Phase 0 complete: FastAPI/uvicorn import cleanly, CI runs, retry logic in LLM clients.
- Understanding of: `GameEngine` (`game.py`), `MatchConfig`, `MatchResult`, `TurnLog`, replay JSON format (`cli.py` serialization).
- Understanding of: FastAPI dependency injection, Pydantic response models, async endpoint patterns.

---

## §3 Execution Rules

### MUST DO

- Create `backend/src/llm_smash/api/` package with `app.py` (FastAPI app factory), `routes.py` (endpoints), `schemas.py` (request/response models).
- Implement these REST endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check, returns `{"status": "ok"}` |
| `POST` | `/matches` | Create and start a new match (async background task) |
| `GET` | `/matches` | List recent matches with summary info |
| `GET` | `/matches/{match_id}` | Get match result (status, winner, turn count, etc.) |
| `GET` | `/matches/{match_id}/turns` | Get full turn-by-turn log |
| `GET` | `/matches/{match_id}/replay` | Get replay JSON (same format as CLI replay files) |
| `GET` | `/archetypes` | List available fighter archetypes with stats |

- Match execution must run as a FastAPI `BackgroundTask` or via `asyncio.create_task`, not blocking the request.
- Use an in-memory store (`dict[str, MatchResult]`) for match results. No database in v0.2.0.
- Reuse the existing `GameEngine` and `MockLLMClient` — do not rewrite the engine.
- Add a `--serve` flag to `__main__.py` that starts the API server instead of running a CLI match.
- Write API tests using `httpx.AsyncClient` and FastAPI's `TestClient`.
- All existing tests must continue to pass.

### MUST NOT DO

- Do not add a database or persistent storage. In-memory `dict` is sufficient for v0.2.0.
- Do not add authentication or authorization.
- Do not add WebSocket endpoints (that is Phase 2).
- Do not add CORS configuration yet (Phase 3 will add it when the frontend exists).
- Do not change the game engine's behavior or the combat system.
- Do not add frontend code.

---

## §4 Task Breakdown

### Task 1.1: Create API Package Structure

```
backend/src/llm_smash/api/
├── __init__.py
├── app.py          # FastAPI app factory
├── routes.py       # endpoint handlers
├── schemas.py      # request/response Pydantic models
└── match_manager.py  # in-memory match storage and execution
```

### Task 1.2: Define Request/Response Schemas

In `schemas.py`:

```python
from pydantic import BaseModel

class MatchCreateRequest(BaseModel):
    fighter1_archetype: str  # "striker", "guardian", etc.
    fighter2_archetype: str
    fighter1_model: str | None = None  # LLM model name, None = mock
    fighter2_model: str | None = None
    max_turns: int = 50
    seed: int | None = None

class MatchSummary(BaseModel):
    match_id: str
    status: str  # "running", "completed", "error"
    fighter1: str
    fighter2: str
    winner: str | None = None
    turn_count: int = 0
    created_at: float  # unix timestamp

class MatchDetail(MatchSummary):
    turns: list[dict]  # serialized TurnLog list
    replay: dict  # full replay JSON
```

Design these to wrap existing engine types (`MatchResult`, `TurnLog`) — do not duplicate state model logic.

### Task 1.3: Implement MatchManager

In `match_manager.py`:

```python
class MatchManager:
    """In-memory match storage and async execution."""

    def __init__(self):
        self._matches: dict[str, MatchRecord] = {}

    async def create_match(self, request: MatchCreateRequest) -> str:
        """Create a match, start it as a background task, return match_id."""
        match_id = str(uuid.uuid4())[:8]
        # Initialize GameEngine with MockLLMClient or real clients
        # Store MatchRecord with status="running"
        # Launch asyncio.create_task(self._run_match(match_id))
        return match_id

    async def _run_match(self, match_id: str):
        """Execute match and store result."""
        # Run GameEngine.run_match()
        # Update MatchRecord with result, status="completed"
        # On exception: status="error", store error message

    def get_match(self, match_id: str) -> MatchRecord | None: ...
    def list_matches(self, limit: int = 20) -> list[MatchRecord]: ...
```

Use a singleton `MatchManager` injected via FastAPI's `Depends()`.

### Task 1.4: Implement REST Endpoints

In `routes.py`:

```python
router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/matches", status_code=201)
async def create_match(request: MatchCreateRequest, manager: MatchManager = Depends(get_manager)):
    match_id = await manager.create_match(request)
    return {"match_id": match_id}

@router.get("/matches")
async def list_matches(limit: int = 20, manager: ...):
    return manager.list_matches(limit)

@router.get("/matches/{match_id}")
async def get_match(match_id: str, manager: ...):
    match = manager.get_match(match_id)
    if not match:
        raise HTTPException(404, "Match not found")
    return match.to_summary()

@router.get("/matches/{match_id}/turns")
async def get_match_turns(match_id: str, manager: ...):
    # Return turn-by-turn log
    ...

@router.get("/matches/{match_id}/replay")
async def get_match_replay(match_id: str, manager: ...):
    # Return replay JSON (same format as CLI replay files)
    ...

@router.get("/archetypes")
async def list_archetypes():
    # Return archetype definitions from roster.py
    ...
```

### Task 1.5: Create FastAPI App Factory

In `app.py`:

```python
from fastapi import FastAPI
from llm_smash.api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Smash Bros API",
        version="0.2.0",
        description="Turn-based AI fighting game — match API",
    )
    app.include_router(router, prefix="/api")
    return app
```

### Task 1.6: Add `--serve` Flag to `__main__.py`

Extend the existing argument parser:

```python
parser.add_argument("--serve", action="store_true", help="Start the API server")
parser.add_argument("--port", type=int, default=8000, help="API server port")

if args.serve:
    import uvicorn
    from llm_smash.api.app import create_app
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
else:
    # existing CLI match logic
    asyncio.run(run_cli_match(...))
```

Verify: `python -m llm_smash --serve` starts the server, `python -m llm_smash` still runs a CLI match.

### Task 1.7: Write API Tests

Create `backend/tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from llm_smash.api.app import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

async def test_create_and_get_match(client):
    # POST /api/matches with mock fighters
    r = await client.post("/api/matches", json={
        "fighter1_archetype": "striker",
        "fighter2_archetype": "guardian",
    })
    assert r.status_code == 201
    match_id = r.json()["match_id"]

    # Poll until completed (with timeout)
    import asyncio
    for _ in range(50):
        r = await client.get(f"/api/matches/{match_id}")
        if r.json()["status"] == "completed":
            break
        await asyncio.sleep(0.1)

    assert r.json()["status"] == "completed"
    assert r.json()["winner"] is not None

async def test_list_matches(client): ...
async def test_get_replay(client): ...
async def test_list_archetypes(client): ...
async def test_match_not_found(client):
    r = await client.get("/api/matches/nonexistent")
    assert r.status_code == 404
```

### Task 1.8: Final Verification

```bash
# All tests pass
cd backend && uv run pytest -q

# API server starts
python -m llm_smash --serve &
curl http://localhost:8000/api/health
# {"status": "ok"}

# Create a mock match via API
curl -X POST http://localhost:8000/api/matches \
  -H "Content-Type: application/json" \
  -d '{"fighter1_archetype": "striker", "fighter2_archetype": "guardian"}'
# {"match_id": "abc12345"}
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Health endpoint works | `/api/health` returns error | Returns `{"status": "ok"}` with 200 |
| 2 | Match creation works | POST `/api/matches` fails | Returns 201 with `match_id`, match runs in background |
| 3 | Match result retrieval works | GET `/api/matches/{id}` fails | Returns match summary with winner after completion |
| 4 | Turn log retrieval works | GET `/api/matches/{id}/turns` fails | Returns ordered turn-by-turn data |
| 5 | Replay format matches CLI | Replay JSON has different schema than CLI replays | Same replay format as CLI replay files |
| 6 | Archetypes endpoint works | No way to list available fighters | Returns all 4 archetypes with stats and abilities |
| 7 | `--serve` flag works | `python -m llm_smash --serve` crashes | Starts uvicorn on specified port |
| 8 | CLI still works | `python -m llm_smash` broken | CLI match runs as before |
| 9 | API tests pass | No API tests or failures | All API tests green |
| 10 | Existing tests unbroken | Any pre-existing test fails | All 189+ tests still pass |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] `curl /api/health` returns OK.
- [ ] Create a match, wait for it, and retrieve the result — full lifecycle works.
- [ ] Read the replay JSON from API. Compare structure to a CLI-generated replay file in `replays/`. Same format?
- [ ] Run `python -m llm_smash` (no `--serve`). CLI still works normally?
- [ ] Run full test suite. All green?
- [ ] Read `match_manager.py`. Is there a risk of match tasks leaking (never cleaned up)? Add a max match limit if needed.

---

## §7 Self-Optimization & Retry Guidance

**If match creation hangs:**
- Check if `asyncio.create_task` is used correctly inside the FastAPI event loop.
- Ensure `GameEngine.run_match()` is truly async (it is — but verify the mock client's `asyncio.sleep` works in this context).

**If replay format diverges from CLI:**
- Read `cli.py`'s replay serialization logic. The API replay endpoint should use the exact same serialization.
- Consider extracting replay serialization into a shared utility if it's duplicated.

**If tests are slow:**
- Mock match tests may take 1-2s each due to simulated turns. This is acceptable.
- If >5s per test, check if `MockLLMClient.latency` is too high.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

---

## §9 Next Phase Pointer

**Next:** Phase 2 — WebSocket Match Streaming (`docs/dev/0.2.0/phase-2-websocket-streaming.md`)

**What Phase 2 needs from this phase:**
- Working FastAPI app with match lifecycle management.
- `MatchManager` that can expose match state during execution (not just after).
- `create_app()` factory that Phase 2 can extend with WebSocket routes.

**What Phase 2 does NOT need from this phase:**
- Any WebSocket code.
- CORS configuration (Phase 3).
- Frontend (Phase 3+).

# Phase 6 — Integration, Polish & Deployment

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 6`
**Prerequisites:** Phase 5 complete (all pages working, replay browser, shared components)

---

## §1 Phase Goal & Purpose

Prove the entire system works end-to-end, polish the rough edges, and make the project **deployable as a single unit**. This is the "ship it" phase — after this, someone can clone the repo, run two commands, and have a working web-based LLM fighting game.

**Why this matters:**
- Phases 0-5 built features in isolation. This phase verifies they connect correctly: lobby → API → engine → WebSocket → frontend → replay. Any broken handshake here means the product doesn't work.
- First impressions matter. Visual inconsistencies, broken edge cases, and ugly error states will undermine the "this is a real product" perception.
- Deployment packaging (Docker or simple scripts) determines whether anyone outside the developer's machine can use this.
- Per `STRATEGY §2.2`, authenticity matters. The web experience must feel as polished as the CLI experience that closed v0.1.0.

---

## §2 Prerequisites & Dependencies

- Phase 5 complete: all pages (lobby, live match, history, replay) working.
- Backend API + WebSocket + CLI all functional.
- Understanding of: Docker basics, Vite build output, FastAPI static file serving.

---

## §3 Execution Rules

### MUST DO

- Write **end-to-end integration tests** that exercise the full stack: create match via API → connect WebSocket → receive turns → verify result matches REST endpoint.
- Write **frontend smoke tests** (lightweight: does it render without crashing).
- Fix visual bugs and edge cases found during E2E testing.
- Add **error states** to the frontend: API unreachable, WebSocket disconnected, match not found, invalid replay file.
- Add a **loading state** for match creation (spinner while match starts).
- Create a **production build pipeline**: `frontend/` builds to static files, FastAPI serves them alongside the API.
- Create a **Docker Compose setup** with a single `docker-compose up` that runs the full stack.
- Write a **quickstart section** in README for the web mode.
- Verify the v0.2.0 exit criteria.
- All tests (backend + frontend smoke) pass.

### MUST NOT DO

- Do not add new features. This phase is integration, polish, and packaging.
- Do not add HTTPS/SSL (deployment environment handles that).
- Do not add user authentication.
- Do not add analytics or telemetry.
- Do not change game mechanics.
- Do not deploy to a cloud provider (document how, but do not do it in this phase).

---

## §4 Task Breakdown

### Task 6.1: End-to-End Integration Tests

Create `backend/tests/test_e2e.py`:

```python
"""End-to-end tests exercising the full API + WebSocket + Engine stack."""

async def test_full_match_lifecycle(client, ws_client):
    """
    1. POST /api/matches → get match_id
    2. Connect WebSocket to /api/matches/{id}/ws
    3. Receive match_start message
    4. Receive turn messages (at least 1)
    5. Receive match_end message with winner
    6. GET /api/matches/{id} → status=completed, winner matches
    7. GET /api/matches/{id}/replay → valid replay JSON
    8. GET /api/matches → match appears in list
    """
    ...

async def test_multiple_concurrent_matches(client):
    """Start 3 matches simultaneously. All should complete without interference."""
    ...

async def test_match_with_all_archetype_combinations(client):
    """Run all 6 unique matchups (4 choose 2). All should complete."""
    ...

async def test_replay_matches_live_result(client, ws_client):
    """
    Replay JSON from API should contain the same turns
    that were streamed via WebSocket during the match.
    """
    ...

async def test_late_join_receives_state_sync(client, ws_client):
    """
    Start a match, wait for a few turns, then connect WebSocket.
    Should receive state_sync with past turns, then continue receiving live turns.
    """
    ...
```

### Task 6.2: Frontend Smoke Tests

Add basic render tests using Vitest (already bundled with Vite):

```bash
cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

```typescript
// src/components/__tests__/ArenaGrid.test.tsx
import { render, screen } from "@testing-library/react";
import { ArenaGrid } from "../ArenaGrid";
import { MOCK_STATE } from "../../data/mockState";

test("ArenaGrid renders correct number of cells", () => {
  render(<ArenaGrid arena={MOCK_STATE.arena} fighters={MOCK_STATE.fighters} />);
  const cells = document.querySelectorAll(".cell");
  expect(cells.length).toBe(48); // 8x6
});

test("FighterPanel shows HP percentage", () => { ... });
test("MatchLayout renders without crashing", () => { ... });
test("LobbyPage renders archetype selectors", () => { ... });
```

Add to `package.json`:
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

### Task 6.3: Error States

Add error handling UI for these scenarios:

**API unreachable:**
```
┌──────────────────────────────┐
│  ⚠ Cannot reach game server │
│  Make sure the backend is    │
│  running on port 8000.       │
│                              │
│  [Retry]                     │
└──────────────────────────────┘
```

**WebSocket disconnected mid-match:**
```
┌──────────────────────────────┐
│  ⚠ Connection lost          │
│  Attempting to reconnect...  │
│  (attempt 2/3)               │
└──────────────────────────────┘
```

**Match not found (404):**
```
┌──────────────────────────────┐
│  ⚠ Match not found          │
│  This match may have expired │
│  from the server's memory.   │
│                              │
│  [Go to Lobby]               │
└──────────────────────────────┘
```

**Invalid replay file:**
```
┌──────────────────────────────┐
│  ⚠ Invalid replay file      │
│  The file could not be       │
│  parsed as a valid replay.   │
│                              │
│  [Try Another File]          │
└──────────────────────────────┘
```

### Task 6.4: Loading States

Add loading indicators:

- **Match creation:** "Starting match..." spinner after clicking "Fight!" (while waiting for POST response and WebSocket connection).
- **History page:** skeleton cards while fetching match list.
- **Replay loading:** "Loading replay..." while fetching replay JSON.

### Task 6.5: Production Build — Static File Serving

Configure FastAPI to serve the built frontend as static files in production:

```python
# In app.py
import os
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI(...)
    # ... API routes ...

    # Serve frontend static files in production
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app
```

Build pipeline:
```bash
cd frontend && npm run build   # outputs to frontend/dist/
cd backend && python -m llm_smash --serve  # serves API + static files
# Visit http://localhost:8000 → frontend loads
```

### Task 6.6: Docker Compose Setup

Create `docker-compose.yml` at repo root:

```yaml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    command: python -m llm_smash --serve --port 8000
```

Create `Dockerfile` at repo root:

```dockerfile
FROM python:3.12-slim

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Build frontend
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
RUN cd frontend && npm run build

# Install backend
COPY backend/pyproject.toml backend/uv.lock* backend/
RUN cd backend && uv sync --no-dev
COPY backend/ backend/

EXPOSE 8000
CMD ["uv", "run", "--directory", "backend", "python", "-m", "llm_smash", "--serve", "--port", "8000"]
```

Verify:
```bash
docker-compose up --build
# Visit http://localhost:8000 → full app works
```

### Task 6.7: Update README for Web Mode

Add a "Web Mode" section to `README.md`:

```markdown
## Web Mode (v0.2.0)

### Quick Start

```bash
# Option 1: Docker (recommended)
docker-compose up --build
# Open http://localhost:8000

# Option 2: Manual
cd frontend && npm install && npm run build
cd ../backend && uv sync
python -m llm_smash --serve
# Open http://localhost:8000
```

### Development Mode

```bash
# Terminal 1: Backend API
cd backend && python -m llm_smash --serve

# Terminal 2: Frontend dev server
cd frontend && npm run dev
# Open http://localhost:5173
```
```

### Task 6.8: Visual Polish Pass

Review all pages and fix:

- [ ] Consistent spacing and padding across all pages.
- [ ] All text readable at 1280x720 resolution.
- [ ] Hazard indicators visible over terrain colors.
- [ ] HP bar at 0% doesn't look broken (1px minimum or empty state).
- [ ] Long model names don't break layout (text-overflow: ellipsis).
- [ ] Turn 50/50 (max turns) shows the draw state correctly.
- [ ] Empty match history page shows a friendly message, not a blank page.

### Task 6.9: Final Verification — Exit Criteria

Verify all v0.2.0 exit criteria:

```
- [ ] A user can start a match from a browser and watch it live
- [ ] Turn-by-turn WebSocket streaming delivers real-time updates
- [ ] Arena grid with terrain renders correctly in the browser
- [ ] Fighter status (HP, energy, effects) is visible and updates live
- [ ] Tactical summaries and trash talk are displayed each turn
- [ ] Match history page lists completed matches
- [ ] Replays can be loaded and played back with controls
- [ ] CLI replay JSON files can be uploaded and viewed in the browser
- [ ] The full stack can be deployed with Docker
- [ ] All backend tests pass
- [ ] Frontend smoke tests pass
- [ ] The web experience is polished enough for a demo
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | E2E test passes | Full lifecycle test fails | Match creation → WS stream → result → replay verified |
| 2 | Concurrent matches work | Matches interfere with each other | 3 simultaneous matches all complete correctly |
| 3 | Frontend smoke tests pass | Component render tests fail | All smoke tests green |
| 4 | Error states handled | Errors show white screen or crash | User-friendly error messages for all failure modes |
| 5 | Loading states exist | Buttons feel broken (no feedback) | Spinners/skeletons shown during async operations |
| 6 | Production build works | `npm run build` fails or app doesn't serve | Single server serves API + frontend |
| 7 | Docker build works | `docker-compose up` fails | Full stack runs in Docker |
| 8 | README updated | No web mode docs | Quickstart guide for web mode |
| 9 | Visual polish complete | Broken layouts, unreadable text | Consistent, readable, 1280x720-compatible |
| 10 | All v0.2.0 exit criteria met | Any exit criterion fails | All 12 exit criteria checked |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Fresh `git clone` → `docker-compose up` → browser → lobby → fight → watch → replay. Does the entire flow work from scratch?
- [ ] Open the app at 1280x720. Is everything readable?
- [ ] Disconnect the network mid-match. Does the frontend show an error?
- [ ] Stop the backend mid-match. Does the frontend recover gracefully?
- [ ] Upload a CLI replay from `replays/`. Does it play correctly?
- [ ] Run `cd backend && uv run pytest -q`. All green?
- [ ] Run `cd frontend && npm test`. All green?
- [ ] Would you show this to someone and feel confident it "works"?

---

## §7 Self-Optimization & Retry Guidance

**If E2E tests are flaky:**
- Mock matches with `MockLLMClient` have randomized behavior but deterministic RNG with seeds. Pass a fixed seed in E2E tests for reproducibility.
- Add generous timeouts for match completion (mock matches take ~1-5 seconds).

**If Docker build is slow:**
- Layer the Dockerfile correctly: package.json/pyproject.toml before source code. Node modules and Python deps will be cached.

**If static file serving conflicts with API routes:**
- Ensure API routes (`/api/*`) are mounted BEFORE the static file catch-all (`/`).
- Use `app.mount("/", StaticFiles(...), name="frontend")` as the last mount.

**If visual polish is taking too long:**
- Prioritize: arena rendering > HP bars > match conclusion > everything else.
- "Looks intentionally minimalist" is better than "looks half-finished."

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

---

## §9 Milestone Closeout

After this phase completes successfully, v0.2.0 is done. Update:

- `PLAN.md` — check all v0.2.0 exit criteria, add writeback.
- `STRATEGY.md` — update priorities for v0.3.0 (expanded arena: new archetypes, audience interaction, AI commentator).
- `backend/pyproject.toml` — bump version to `0.2.0`.
- `README.md` — final v0.2.0 feature list.
- Git tag: `v0.2.0`.

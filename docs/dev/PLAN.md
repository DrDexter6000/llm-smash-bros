# LLM Smash Bros — Roadmap & Implementation Plan

**Version:** 0.5.0
**Last Updated:** 2026-04-08
**Authority:** Roadmap/execution document; subordinate to `STRATEGY.md` and `PRD.md`
**Read after:** `STRATEGY.md`, `PRD.md`

---

## 1. Strategic Rationale

The project has passed the "can this technically work?" stage. The backend can run real LLM matches. The next milestone transforms the project from an engineering proof into a **fair, watchable evaluation arena**.

Per `STRATEGY §3`, the v0.1.0 milestone prioritizes:

1. Foundation integrity (fix bugs, remove lying prompts),
2. Fair archetype system (decouple fighters from LLM brands),
3. Spatial strategy (terrain gives positioning real meaning),
4. Battle memory and prompt contract (enable multi-turn reasoning, spectator-readable output),
5. Spectator-ready CLI (terminal-first, OBS-streamable),
6. Balance and credibility (evidence that matches reflect model quality).

---

## 2. Pre-0.1.0 Completed Work

### Phase A — Core Engine Foundations ✅

Delivered: battle state models, combat resolution, roster definitions, response validation, mock adapter, game loop.

Exit condition met: the project can simulate complete matches locally.

### Phase B — Live LLM Backend ✅

Delivered: OpenAI-compatible client, Anthropic-compatible client, live environment wiring, preflight checks, configurable timeouts, validator hardening for markdown and `<think>` wrappers.

Exit condition met: the project can complete a real live match with external LLMs.

---

## 3. Planning Rules

### 3.1 Milestone Structure

v0.1.0 is organized into 6 phases with detailed TDD plans in `docs/dev/0.1.0/`. This file tracks phase-level status. Execution details live in the phase plans.

### 3.2 Phase Execution Protocol

Each phase plan in `docs/dev/0.1.0/` follows a closed-loop structure:

1. **Goal** — what the phase delivers and why.
2. **Execution Rules** — what to do and what not to do.
3. **Tasks** — specific implementation work.
4. **Acceptance Criteria** — red/green pass conditions.
5. **Self-Audit** — what to check after implementation.
6. **Self-Optimization** — what to retry or improve if the first pass is weak.
7. **Execution Writeback** — mandatory post-completion summary appended to the plan.
8. **Next Phase Pointer** — what comes next and what it depends on from this phase.

### 3.3 Dependency Chain

```
Phase 1 (Cleanup) → Phase 2 (Archetypes) → Phase 3 (Terrain) → Phase 4 (Prompt Contract)
                                                                         ↓
                                                              Phase 5 (Rich CLI)
                                                                         ↓
                                                              Phase 6 (Balance)
```

Phases 1→2→3→4 are strictly sequential (each builds on the prior). Phase 5 depends on Phase 4 (needs new prompt contract for display). Phase 6 depends on Phase 5 (needs the full system running to measure balance).

---

## 4. v0.1.0 Phase Overview

### Phase 1 — Foundation Cleanup

**Goal:** Fix known bugs and mechanical debt so the codebase is honest and stable.

**Key Deliverables:**
- Fix `__main__.py` duplicate code bug
- Remove or rewrite ability descriptions that reference unimplemented effects
- Add `.gitignore` rules for `.env` files
- Green test suite

**TDD Plan:** `docs/dev/0.1.0/phase-1-foundation-cleanup.md`

### Phase 2 — Archetype System

**Goal:** Replace the LLM-branded fighter roster with generic, balanced archetypes.

**Key Deliverables:**
- 4 archetype definitions (Striker, Guardian, Controller, Berserker)
- Each with 4 abilities (basic + 2 tactical + ultimate)
- All ability effects implemented in the combat engine
- Updated system prompts with archetype identity layer
- Match config supports any model → any archetype mapping

**TDD Plan:** `docs/dev/0.1.0/phase-2-archetype-system.md`

### Phase 3 — Terrain & Spatial Strategy

**Goal:** Add terrain types so positioning creates real tactical decisions.

**Key Deliverables:**
- 3 terrain types (High Ground, Cover, Rift)
- Symmetric random terrain generation
- Combat resolver terrain modifiers
- ASCII grid representation for LLM prompts

**TDD Plan:** `docs/dev/0.1.0/phase-3-terrain-spatial.md`

### Phase 4 — Battle Memory & Prompt Contract

**Goal:** Enable multi-turn reasoning and produce spectator-readable output.

**Key Deliverables:**
- Recent turns history (last 3 turns) injected into battle state
- New output schema: `tactical_summary` replaces `inner_monologue`
- Archetype-specific strategic identity in system prompts
- Updated validator for new schema
- Total prompt under 2000 tokens

**TDD Plan:** `docs/dev/0.1.0/phase-4-battle-memory-prompt.md`

### Phase 5 — Rich CLI & Spectator Layer

**Goal:** Terminal output polished enough to record/stream via OBS.

**Key Deliverables:**
- Migrate from raw ANSI to `rich` library
- Panel-based battle display with terrain grid
- Fumble comedy display (raw gibberish as content)
- Match replay serialization (full match → JSON file)

**TDD Plan:** `docs/dev/0.1.0/phase-5-rich-cli.md`

### Phase 6 — Integration, Balance & Verification

**Goal:** Evidence that the system works end-to-end and that matches are credible.

**Key Deliverables:**
- Integration tests (full mock match simulation)
- Batch match runner (N matches for statistical analysis)
- Per-archetype and per-model fumble rate measurement
- Randomness-vs-skill analysis
- v0.1.0 exit criteria verification

**TDD Plan:** `docs/dev/0.1.0/phase-6-integration-balance.md`

---

## 5. v0.2.0 — Web Spectator Layer

### Strategic Rationale

v0.1.0 proved the engine produces compelling content. v0.2.0 proves the content is **watchable in a browser** — the format that enables sharing, embedding, streaming, and viral spread. The milestone transforms the project from a developer tool into a spectator-ready product.

### Dependency Chain

```
Phase 0 (Hygiene) → Phase 1 (API Server) → Phase 2 (WebSocket) → Phase 3 (Frontend)
                                                                         ↓
                                                              Phase 4 (Live Viewer)
                                                                         ↓
                                                              Phase 5 (Replays)
                                                                         ↓
                                                              Phase 6 (Integration)
```

Phases 0→1→2→3 are strictly sequential. Phase 4 depends on Phase 3 (needs visual components + WebSocket). Phase 5 depends on Phase 4 (reuses live viewer components). Phase 6 depends on Phase 5 (verifies the full system).

### Phase 0 — Engineering Hygiene

**Goal:** Harden the engineering foundation before building the web layer.

**Key Deliverables:**
- GitHub Actions CI pipeline
- Root-level pytest fix
- API retry logic with exponential backoff
- Dependency verification

**TDD Plan:** `docs/dev/0.2.0/phase-0-engineering-hygiene.md`

### Phase 1 — API Server Foundation

**Goal:** Turn the CLI-only engine into a headless match service via FastAPI REST endpoints.

**Key Deliverables:**
- REST endpoints: health, create match, list matches, get result, get turns, get replay, list archetypes
- In-memory MatchManager with background match execution
- `--serve` flag for `__main__.py`
- API tests

**TDD Plan:** `docs/dev/0.2.0/phase-1-api-server.md`

### Phase 2 — WebSocket Match Streaming

**Goal:** Real-time turn-by-turn streaming for live spectating.

**Key Deliverables:**
- WebSocket endpoint at `/api/matches/{id}/ws`
- ConnectionManager with multi-spectator broadcast
- Late-join state sync
- WebSocket message protocol (match_start, turn, match_end, state_sync)

**TDD Plan:** `docs/dev/0.2.0/phase-2-websocket-streaming.md`

### Phase 3 — Frontend Scaffold & Arena Renderer

**Goal:** React + TypeScript app with the core arena grid and fighter status components.

**Key Deliverables:**
- Vite + React + TypeScript scaffold in `frontend/`
- ArenaGrid component (8x6 CSS Grid with terrain colors)
- FighterToken and FighterPanel components
- TypeScript types mirroring backend Pydantic models
- Dark fighting game theme
- CORS middleware on FastAPI

**TDD Plan:** `docs/dev/0.2.0/phase-3-frontend-scaffold.md`

### Phase 4 — Live Battle Viewer

**Goal:** Wire WebSocket to frontend — real-time match viewing with transitions and drama.

**Key Deliverables:**
- useMatchWebSocket hook
- Turn pacing queue (1.5s per turn)
- LobbyPage (archetype selection, fight button)
- MatchPage (animated turn resolution, tactical summaries, trash talk)
- CSS transitions (movement, HP bars, damage numbers)
- Match intro and conclusion screens
- Playback controls (pause, speed, skip)

**TDD Plan:** `docs/dev/0.2.0/phase-4-live-battle-viewer.md`

### Phase 5 — Replay Browser & Match History

**Goal:** Browse past matches and re-watch replays with full playback controls.

**Key Deliverables:**
- React Router for multi-page navigation
- MatchHistoryPage (list completed matches)
- ReplayPage (turn-by-turn replay with scrub, step, speed controls)
- Replay file upload (drag-and-drop CLI replay JSON)
- Shared MatchView component for live and replay modes

**TDD Plan:** `docs/dev/0.2.0/phase-5-replay-browser.md`

### Phase 6 — Integration, Polish & Deployment

**Goal:** Prove E2E, polish edges, make it deployable.

**Key Deliverables:**
- End-to-end integration tests
- Frontend smoke tests (Vitest)
- Error states and loading states
- Production build (FastAPI serves frontend static files)
- Docker Compose single-command deployment
- README web mode documentation
- Visual polish pass
- v0.2.0 exit criteria verification

**TDD Plan:** `docs/dev/0.2.0/phase-6-integration-polish.md`

---

## 6. v0.2.0 Exit Criteria

The milestone is complete when all of the following are true:

- [x] A user can start a match from a browser and watch it live
- [x] Turn-by-turn WebSocket streaming delivers real-time updates
- [x] Arena grid with terrain renders correctly in the browser
- [x] Fighter status (HP, energy, effects) is visible and updates live
- [x] Tactical summaries and trash talk are displayed each turn
- [x] Match history page lists completed matches
- [x] Replays can be loaded and played back with controls (pause, speed, scrub, step)
- [x] CLI replay JSON files can be uploaded and viewed in the browser
- [x] The full stack can be deployed with `docker-compose up`
- [x] All backend tests pass
- [x] Frontend smoke tests pass
- [x] The web experience is polished enough for a demo / screenshot

---

## 7. Later Milestones (Post v0.2.0)

These are directional only. Do not plan or execute until v0.2.0 is complete.

### v0.3.0 — Expanded Arena

- Additional archetypes (Summoner? Support?)
- Audience interaction (viewer-triggered chaos)
- AI commentator / TTS integration
- Sound effects

### v0.4.0 — Tournament & Meta

- Tournament bracket system
- ELO tracking across matches
- Content packaging for streaming platforms

---

## 8. v0.1.0 Exit Criteria (Completed)

All criteria met as of 2026-04-07:

- [x] Fighter archetypes are generic and decoupled from LLM identity
- [x] Terrain exists and creates meaningful positioning decisions
- [x] Models receive turn history and produce spectator-readable tactical summaries
- [x] A live match clearly uses real model-generated actions
- [x] Terminal output is polished enough to record/stream via OBS
- [x] Every ability described in prompts has a working engine implementation
- [x] Match outcomes correlate more with tactical quality than random variance
- [x] Mirror matches visibly showcase model differences
- [x] All tests pass, including integration tests

---

## 9. Deferred / Deprioritized Work

The following must not take priority over v0.2.0 phases:

- Additional archetypes beyond the initial 4
- Audience interaction systems
- AI commentator / TTS
- Tournament bracket or ELO systems
- Sound effects or music
- Video/GIF export
- User authentication
- Database persistence (in-memory is sufficient for v0.2.0)
- Cloud deployment (document how, but do not execute)

---

## 10. Documentation Responsibility

If this file proposes work that changes product meaning or conflicts with strategy, the higher document must be updated or this file must be corrected.

Phase-level execution details belong in `docs/dev/0.1.0/` plans, not in this file. This file tracks status and provides navigation.

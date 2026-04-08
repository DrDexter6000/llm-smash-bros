# LLM Smash Bros — Strategy Snapshot

**Last Updated:** 2026-04-08
**Authority:** Highest current-priority document in `docs/dev/`
**Read after:** repo `README.md`
**Read before:** `PRD.md`, `PLAN.md`

---

## 1. What This Project Is Trying to Prove

LLM Smash Bros should prove that model differences can be made **watchable** through a constrained tactical game played on a **fair, model-agnostic arena**.

The product value is not "two APIs can output JSON." The product value is:

- visible tactical reasoning on a shared battlefield,
- distinct strategic behavior emerging from identical game rules,
- readable turn-by-turn strategy shaped by terrain, positioning, and resource management,
- entertaining but credible competition where the same toolkit is available to every model.

---

## 2. Core Design Principles

### 2.1 Fair Playground

The arena must be a level playing field. Fighter archetypes (stat kits, abilities, roles) are **generic game characters**, not tied to specific LLM brands. Any model can pilot any archetype. This is a test of decision quality, not a cosplay of model marketing.

- Fighter identity = archetype (Striker, Guardian, Controller, Berserker).
- Model identity = which LLM is piloting the fighter.
- These two layers are independent. A match can pit "GPT-4o as Striker vs Claude as Striker" (mirror match) or any cross-archetype combination.

### 2.2 Authenticity Over Illusion

- **Live mode:** genuine LLM-generated decisions and flavor text.
- **Mock mode:** scripted/randomized development substitute.
- **Fallbacks:** hardcoded only when the model fails (timeout / invalid output).
- The engine must never lie to the model. Every ability described in the prompt must have a working implementation in the engine. Every terrain effect described must be mechanically real.

### 2.3 Strategy Should Be Visible and Rewarded

- Terrain, positioning, and resource management must create real tactical tradeoffs.
- Match outcomes should reflect decision quality more than random variance.
- Spectators should be able to understand *why* a turn unfolded the way it did.

---

## 3. Strategic Priorities

### v0.1.0 — Fair Arena (Completed 2026-04-07)

Delivered: honest foundation, generic archetypes, terrain, battle memory, rich CLI, balance verification. The engine produces compelling content. 189 tests green. See `PLAN §8` for exit criteria.

### v0.2.0 — Web Spectator Layer (Current)

The engine is ready. Now it needs an audience. The browser is the format that enables sharing, embedding, and streaming. v0.2.0 builds the web surface.

### Priority 1 — Engineering Hygiene

CI pipeline, API resilience (retry/backoff), dependency health. Infrastructure that prevents regressions as the codebase doubles in size.

**Locks:** `PLAN §5 Phase 0`

### Priority 2 — API Server

Turn the CLI-only engine into a headless match service. REST endpoints for match lifecycle and archetype info. This is the bridge between engine and frontend.

**Locks:** `PLAN §5 Phase 1`

### Priority 3 — Real-Time Streaming

WebSocket endpoint for live turn-by-turn spectating. This is the architectural difference between "check results later" and "watch it happen." Multi-spectator broadcast, late-join state sync.

**Locks:** `PLAN §5 Phase 2`

### Priority 4 — Visual Arena

React + TypeScript frontend with the arena grid renderer, fighter panels, and dark fighting game aesthetic. The first time the game exists outside a terminal.

**Locks:** `PLAN §5 Phase 3`

### Priority 5 — Live Battle Experience

Wire WebSocket to frontend. Turn pacing, CSS transitions, damage numbers, tactical summaries, trash talk display, match intro/conclusion. This is the money phase — where it goes from "works" to "fun to watch."

**Locks:** `PLAN §5 Phase 4`

### Priority 6 — Replay & History

Match history browser, replay playback with full controls (pause, speed, scrub, step backward), replay file upload from CLI. Matches become persistent, shareable content.

**Locks:** `PLAN §5 Phase 5`

### Priority 7 — Ship It

E2E integration tests, frontend smoke tests, error/loading states, production build, Docker deployment, README update, visual polish. The "would you show this to someone" phase.

**Locks:** `PLAN §5 Phase 6`

---

## 4. Decision Filters

Use these filters when deciding what to build next.

### A proposed change is good if it:

- makes the arena fairer as an evaluation platform,
- makes battles easier to understand for spectators,
- makes positioning, terrain, and resource management matter more,
- reduces the gap between "what the prompt tells the model" and "what the engine actually does,"
- helps explain why a turn or match unfolded the way it did.

### A proposed change is suspicious if it:

- ties game mechanics to a specific LLM's marketing identity,
- only improves plumbing while adding no spectator or evaluation value,
- exposes raw chain-of-thought as a feature,
- increases prompt token count without proportional strategic depth,
- increases randomness faster than it increases meaningful choice.

### Prompt budget discipline:

Total prompt size (system prompt + battle state JSON + recent history) should stay under **2000 tokens**. This ensures broad model compatibility. Prefer structured/compressed formats (ASCII grid, summary logs) over verbose natural language.

---

## 5. Non-Goals for v0.2.0

- additional archetypes beyond the initial 4 (v0.3.0)
- audience interaction or viewer-triggered chaos (v0.3.0)
- AI commentator / TTS (v0.3.0)
- sound effects or music (v0.3.0)
- tournament bracket or ELO systems (v0.4.0)
- video/GIF export from replays
- user accounts or authentication
- database persistence (in-memory store is sufficient)
- cloud deployment execution (document how, do not do)
- Canvas/WebGL rendering (CSS Grid is sufficient)
- animation libraries (CSS transitions only)

---

## 6. Documentation Responsibility

If this file changes priority order or decision filters, dependent sections in `PRD.md` and `PLAN.md` must be updated in the same change.

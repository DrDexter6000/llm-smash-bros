# LLM Smash Bros — Strategy Snapshot

**Last Updated:** 2026-04-07
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

## 3. Strategic Priorities (v0.1.0)

### Priority 1 — Foundation Integrity

Fix known bugs and mechanical debt. Remove any prompt content that describes unimplemented mechanics. The codebase must be honest before new features are added.

**Locks:** `PLAN §4 Phase 1`

### Priority 2 — Fair Archetype System

Replace the current LLM-branded fighter roster with generic, balanced archetypes. Decouple "who the fighter is" from "which model is playing." This is the single most important architectural change for the project's evaluation credibility.

**Locks:** `PRD §5`, `PLAN §4 Phase 2`

### Priority 3 — Spatial Strategy (Terrain)

Add terrain types to the arena so positioning has real tactical meaning. Movement should matter. The board should create interesting choices every turn, not just be a flat grid.

**Locks:** `PRD §6`, `PLAN §4 Phase 3`

### Priority 4 — Battle Memory & Prompt Contract

Give models access to recent turn history so they can do multi-turn reasoning. Redesign the prompt output contract to produce spectator-readable tactical summaries instead of raw inner monologue.

**Locks:** `PRD §7`, `PLAN §4 Phase 4`

### Priority 5 — Spectator-Ready CLI

Migrate terminal output to `rich` for a polished, OBS-streamable terminal experience. This is the fastest path to audience validation.

**Locks:** `PRD §4`, `PLAN §4 Phase 5`

### Priority 6 — Balance & Credibility

Measure and tune: fumble rates, randomness-vs-skill ratio, archetype balance. Produce evidence that matches reflect model quality.

**Locks:** `PRD §10`, `PLAN §4 Phase 6`

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

## 5. Non-Goals for v0.1.0

- exhaustive provider support beyond OpenAI-compatible and Anthropic-compatible
- audience interaction systems
- AI commentator / TTS
- deployment polish before the core match experience is convincing
- tournament meta systems
- web GUI / animation layer (terminal-first for this milestone)
- raw chain-of-thought display as a core feature

---

## 6. Documentation Responsibility

If this file changes priority order or decision filters, dependent sections in `PRD.md` and `PLAN.md` must be updated in the same change.

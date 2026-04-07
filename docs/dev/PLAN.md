# LLM Smash Bros — Roadmap & Implementation Plan

**Version:** 0.3.0  
**Last Updated:** 2026-04-07  
**Authority:** Roadmap/execution document; subordinate to `STRATEGY.md` and `PRD.md`  
**Read after:** `STRATEGY.md`, `PRD.md`

---

## 1. Strategic Rationale

The project has passed the “can this technically work?” stage. The backend can already run real LLM matches, and the main product risk is no longer provider configuration.

Per `STRATEGY §3`, the next phase of work should optimize for **spectator value**, specifically:

1. making model strategy more visible and readable,
2. making the game reward deeper tactical behavior,
3. making the presentation layer feel intentionally designed rather than debug-oriented.

---

## 2. Current Status Snapshot

### 2.1 Implemented Foundations

- backend Python project and state models
- combat engine with movement, damage, energy, cooldowns, and hazards
- fighter roster and personality prompts
- response validator and fumble handling
- mock LLM adapter
- live OpenAI-compatible and Anthropic-compatible adapters
- CLI battle runner
- first successful live match execution

### 2.2 Current Product Truths

- **Live mode** uses genuine LLM-generated actions and flavor text.
- **Mock mode** is a development/testing substitute and is intentionally scripted/randomized.
- Current UX proves the loop, but does not yet deliver spectator-grade strategy presentation.
- Current mechanics allow tactical play, but deeper planning and match interpretability still need work.

---

## 3. Planning Rules

Use this file as the high-level roadmap, not as a dump of every implementation detail.

When a roadmap phase becomes active:

1. keep this file updated at the phase/status level,
2. create or update a more detailed execution plan only if needed,
3. mark completed phases here so the project narrative stays current.

---

## 4. Completed Phases

### Phase A — Core Engine Foundations ✅

Delivered:

- battle state models
- combat resolution
- roster definitions
- response validation
- mock adapter
- game loop

Exit condition met: the project can simulate complete matches locally.

### Phase B — Live LLM Backend ✅

Delivered:

- OpenAI-compatible client
- Anthropic-compatible client
- live environment wiring
- preflight checks
- configurable timeouts
- validator hardening for markdown and `<think>` wrappers

Exit condition met: the project can complete a real live match with external LLMs.

---

## 5. Next Active Roadmap

### Phase C — Public Reasoning Contract

**Goal:** replace the current debug-flavored `inner_monologue` experience with a spectator-friendly reasoning layer.

**Authority Source:** `STRATEGY §3 Priority 1`, `PRD §5`

#### Outcomes

- define a structured public reasoning schema
- update prompts to request short, readable tactical summaries
- update validation to support the new schema
- update CLI output to present reasoning more clearly

#### Why This Matters

This phase directly addresses the biggest product gap: the game currently proves model output, but does not yet package strategy in a watchable way.

### Phase D — Strategy Depth & State Enrichment

**Goal:** make better tactical models visibly outperform weaker ones more often.

**Authority Source:** `STRATEGY §3 Priority 2`, `PRD §6`

#### Outcomes

- enrich battle-state with more strategically useful context
- improve how fighter kits express real tactical tradeoffs
- review whether current randomness is too dominant
- add better post-turn or post-match explainability signals

#### Why This Matters

If the game does not reward planning beyond one-turn reactions, it cannot convincingly showcase meaningful model differences.

### Phase E — Spectator UI / Animation Layer

**Goal:** turn the current CLI proof into a coherent viewer experience.

**Authority Source:** `STRATEGY §3 Priority 3`, `PRD §4`

#### Outcomes

- GUI battle presentation with clear event timing
- animated “thinking / decision / resolve” turn rhythm
- fighter identity presentation through motion, layout, and copy
- readable surfacing of public reasoning and trash talk

#### Why This Matters

The product is supposed to be watched. The UI should make the strategy easier to consume, not just mirror backend events.

### Phase F — Balance, Evaluation & Trustworthiness

**Goal:** make match outcomes more credible and easier to interpret.

**Authority Source:** `STRATEGY §3 Priority 4`, `PRD §10`

#### Outcomes

- evaluate randomness vs skill contribution
- measure fumble rate, invalid output rate, and timeout rate per model
- identify whether certain fighters are strong because of kit design rather than model quality
- produce a repeatable evaluation harness for many matches

#### Why This Matters

Without this phase, viewers may enjoy the spectacle but still not trust what the battles say about the models.

---

## 6. Later Phases

### Phase G — API / Streaming Surfaces

Build network-facing APIs and streaming hooks once the spectator contract is clear.

### Phase H — Audience Interaction

Add viewer-triggered chaos only after the core match experience is readable and trustworthy.

### Phase I — Commentator / TTS / Content Packaging

Only add meta-commentary once the base product already explains itself well.

---

## 7. Near-Term Exit Criteria

Per `PRD §10`, the next roadmap milestone is complete when all of the following are true:

- the product no longer relies on raw-style `inner_monologue` as the primary spectator explanation,
- a viewer can understand turn intent at a glance,
- live battles feel more like strategy showcases than formatting demos,
- the roadmap clearly distinguishes current reality from later ambitions.

---

## 8. Deferred / Deprioritized Work

The following should not take priority over Phases C–F:

- more provider/model plumbing unless it blocks live matches
- broad deployment polish
- tournament systems
- audience chaos features
- raw chain-of-thought visualization

---

## 9. Documentation Responsibility

If this file proposes work that changes product meaning or conflicts with strategy, the higher document must be updated or this file must be corrected.

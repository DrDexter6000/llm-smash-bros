# LLM Smash Bros — Strategy Snapshot

**Last Updated:** 2026-04-07  
**Authority:** Highest current-priority document in `docs/dev/`  
**Read after:** repo `README.md`  
**Read before:** `PRD.md`, `PLAN.md`

---

## 1. What This Project Is Trying to Prove

LLM Smash Bros should prove that model differences can be made **watchable** through a constrained tactical game.

The product value is not “two APIs can output JSON.” The product value is:

- visible tactical reasoning,
- distinct fighter persona,
- readable turn-by-turn strategy,
- entertaining but credible competition.

---

## 2. Known Truths Right Now

### 2.1 Authenticity

- **Live mode:** genuine LLM-generated decisions and flavor text.
- **Mock mode:** scripted/randomized development substitute.
- **Fallbacks:** hardcoded only when the model fails (timeout / invalid output).

### 2.2 Product Stage

- The backend is real enough to validate the concept.
- The current CLI is still mostly an engineering proof, not the intended viewer experience.
- The main risk has shifted from technical connectivity to product clarity.

### 2.3 Current Weaknesses

- reasoning is not yet packaged for spectators,
- deeper strategy is still under-rewarded,
- randomness can blur skill,
- docs must stay lean while becoming more authoritative.

---

## 3. Strategic Priorities

### Priority 1 — Structured Public Reasoning

Replace raw-feeling monologue output with short, readable tactical summaries designed for display.

**Locks:** `PRD §5`, `PLAN §5 Phase C`

### Priority 2 — Deeper Tactical Surface

Improve battle-state and mechanics so stronger planning creates more visible advantages.

**Locks:** `PRD §6`, `PLAN §5 Phase D`

### Priority 3 — Spectator Experience

Build an interface that makes the turn rhythm dramatic and understandable: thinking, intent reveal, action, aftermath.

**Locks:** `PRD §4`, `PLAN §5 Phase E`

### Priority 4 — Credibility

Reduce ambiguity about whether wins come from strategy, luck, or formatting/fumble noise.

**Locks:** `PRD §10`, `PLAN §5 Phase F`

---

## 4. Decision Filters

Use these filters when deciding what to build next.

### A proposed change is good if it:

- makes battles easier to understand,
- makes models feel more distinct,
- increases the amount of meaningful tactical choice,
- reduces “this is just a scripted demo” suspicion,
- helps explain why a turn or match unfolded the way it did.

### A proposed change is suspicious if it:

- only improves plumbing while adding little spectator value,
- exposes raw chain-of-thought as a feature,
- adds spectacle while making strategy harder to read,
- increases randomness faster than it increases interesting choice.

---

## 5. Non-Goals for Now

- exhaustive provider support
- audience interaction systems
- AI commentator / TTS
- deployment polish before the core watch experience is convincing
- tournament meta systems

---

## 6. Documentation Responsibility

If this file changes priority order or decision filters, dependent sections in `PRD.md` and `PLAN.md` must be updated in the same change.

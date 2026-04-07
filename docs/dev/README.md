# Development Docs SSOT Guide

**Last Updated:** 2026-04-07

This directory contains the lean SSOT set for development work. It is intentionally small.

---

## 1. Authority Hierarchy (Conflict Resolution)

When documents conflict, the higher-authority document wins.

1. **`STRATEGY.md`** — highest authority for current priorities, decision filters, and what matters now.
2. **`PRD.md`** — highest authority for product definition, scope, and long-lived requirements.
3. **`PLAN.md`** — highest authority for roadmap sequencing, current execution focus, and phase ordering.

### Locking Rule

- Lower documents must not contradict higher documents.
- If a higher document changes in a way that invalidates a lower document, update the lower document in the **same change**.
- `PLAN.md` may add implementation detail, but it may not redefine product intent.

---

## 2. Reading Order (Macro → Detail)

New contributors should read in this order:

1. **Repo `README.md`** — what the project is, quick orientation
2. **`docs/dev/STRATEGY.md`** — what matters right now and how to make tradeoffs
3. **`docs/dev/PRD.md`** — what the product is supposed to become
4. **`docs/dev/PLAN.md`** — what is done, what is next, and what should not be prioritized yet
5. **`docs/dev/README.md`** — how the SSOT system itself works

This order is mandatory for non-trivial work. Think top-down: **why now → what → how**.

---

## 3. Document Responsibilities

### `STRATEGY.md`

Owns:

- current strategic truth
- current priority order
- decision filters for tradeoffs
- explicit non-goals for the near term

Does **not** own:

- full product spec
- detailed roadmap phases
- implementation checklists

### `PRD.md`

Owns:

- durable product intent
- experience requirements
- scope boundaries
- success criteria
- product risks and open product questions

Does **not** own:

- weekly priority shuffles
- detailed task sequencing
- transient implementation notes

### `PLAN.md`

Owns:

- roadmap phases
- what is complete / active / deferred
- near-term delivery framing
- phase-level execution direction

Does **not** own:

- product redefinition
- conflicting scope changes
- strategy overrides

---

## 4. Reference Discipline

### Stable Reference Format

Use **document + section number** as the authoritative reference.

Examples:

- `STRATEGY §3`
- `PRD §5.2`
- `PLAN §5 Phase C`

This is the canonical cross-reference format because line numbers drift.

### Line Numbers Policy

The user asked for references down to line numbers. We support that with a **line snapshot registry** in this file, but those line numbers are **informational, not authoritative**.

- **Authority anchor:** document + section number
- **Audit anchor:** line snapshot captured on a specific date

If line numbers drift after edits, section-number references remain valid.

---

## 5. Key Cross-Reference Registry

Use this table to lock the most important relationships between docs.

| From | To | Relationship |
|---|---|---|
| `STRATEGY §3 Priority 1` | `PRD §5` | strategy requires a structured public reasoning layer |
| `STRATEGY §3 Priority 2` | `PRD §6` | strategy requires deeper tactical gameplay |
| `STRATEGY §3 Priority 3` | `PRD §4` | strategy requires a spectator-readable match loop |
| `PRD §5` | `PLAN §5 Phase C` | PRD target is implemented through public reasoning work |
| `PRD §6` | `PLAN §5 Phase D` | gameplay requirements are implemented through state/mechanics enrichment |
| `PRD §4` | `PLAN §5 Phase E` | core experience requirements drive spectator UI work |
| `PRD §10` | `PLAN §7` | roadmap exit criteria should satisfy milestone success criteria |

Only register **dependency-grade** links here. Do not bloat this table with casual “see also” references.

---

## 6. Change Protocol

Before changing any development SSOT doc:

1. Identify which document owns the truth you are changing.
2. Check whether the change affects a higher or lower authority doc.
3. Update dependent docs in the same change.
4. If you change section numbering, search for old `§` references and update them.
5. Re-read the docs in macro → detail order if the change is strategic rather than cosmetic.

### Typical Ownership Examples

- “We should prioritize GUI over balancing this month.” → `STRATEGY.md`
- “The product should not expose raw chain-of-thought.” → `PRD.md`
- “Phase C must happen before Phase E.” → `PLAN.md`

---

## 7. Lean Docs Rule

This project should not carry enterprise-grade documentation overhead.

- Prefer 3–4 strong SSOT docs over 20 weak ones.
- Add a new doc only when an existing one can no longer stay readable.
- For a codebase of this size, the current baseline should stay “just enough to build correctly.”

---

## 8. Future Growth Rules

Do **not** pre-create these unless needed:

- `docs/dev/phases/` for large phase execution plans
- `docs/dev/research/` for balancing notes, UX experiments, or evaluation studies
- `docs/dev/adr/` for architecture decisions that deserve permanent records

Only add them when the active SSOT set stops being enough.

---

## 9. TDD Planning Discipline

When `PLAN.md` or any future phase-specific TDD plan is expanded into executable work, the plan should scale to the real workload instead of using fixed ceremony.

- Split into phases, batches, and tasks only when the work size justifies it.
- Each phase should define: goal, execution rules, red/green acceptance, self-audit, self-check/self-optimization, and a writeback section.
- Phase writeback is mandatory: once a phase finishes, append a short execution brief at the end of that phase so the plan remains a living record instead of a stale checklist.
- The end of one phase should make the next step obvious. Plans should preserve a self-looping execution chain rather than stopping at “tasks completed.”

`AGENTS.md` is the repo-level enforcement point for this rule; use this file to understand how it fits into the broader docs system.

---

## 10. Line Snapshot Registry (Informational Only)

These line ranges are a snapshot for auditability as of **2026-04-07**. They are not the source of truth.

| Anchor | File | Line Snapshot |
|---|---|---|
| `STRATEGY §1` | `docs/dev/STRATEGY.md` | lines 10–19 |
| `STRATEGY §3` | `docs/dev/STRATEGY.md` | lines 46–70 |
| `PRD §4` | `docs/dev/PRD.md` | lines 99–137 |
| `PRD §5` | `docs/dev/PRD.md` | lines 141–160 |
| `PRD §6` | `docs/dev/PRD.md` | lines 164–191 |
| `PLAN §5 Phase C` | `docs/dev/PLAN.md` | lines 88–103 |
| `PLAN §5 Phase D` | `docs/dev/PLAN.md` | lines 105–120 |
| `PLAN §5 Phase E` | `docs/dev/PLAN.md` | lines 122–137 |
| `PLAN §7` | `docs/dev/PLAN.md` | lines 174–181 |

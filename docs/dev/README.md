# Development Docs SSOT Guide

**Last Updated:** 2026-04-07

This directory contains the lean SSOT set for development work. It is intentionally small.

---

## 1. Authority Hierarchy (Conflict Resolution)

When documents conflict, the higher-authority document wins.

1. **`STRATEGY.md`** — highest authority for current priorities, decision filters, and what matters now.
2. **`PRD.md`** — highest authority for product definition, scope, and long-lived requirements.
3. **`PLAN.md`** — highest authority for roadmap sequencing, current execution focus, and phase ordering.
4. **`0.1.0/*.md`** — phase-level TDD plans; subordinate to all three above. Owns execution detail for each phase.

### Locking Rule

- Lower documents must not contradict higher documents.
- If a higher document changes in a way that invalidates a lower document, update the lower document in the **same change**.
- `PLAN.md` may add implementation detail, but it may not redefine product intent.
- Phase TDD plans may add task-level detail, but they may not redefine phase scope set by `PLAN.md`.

---

## 2. Reading Order (Macro → Detail)

New contributors (human or AI) should read in this order:

1. **Repo `README.md`** — what the project is, quick orientation
2. **`AGENTS.md`** — repo-level instructions, commands, known traps
3. **`docs/dev/STRATEGY.md`** — what matters right now and how to make tradeoffs
4. **`docs/dev/PRD.md`** — what the product is supposed to become
5. **`docs/dev/PLAN.md`** — what is done, what is next, phase overview
6. **`docs/dev/0.1.0/phase-N-*.md`** — detailed TDD plan for the specific phase you are executing
7. **`docs/dev/README.md`** — how the SSOT system itself works (this file)

This order is mandatory for non-trivial work. Think top-down: **why now → what → how**.

---

## 3. Directory Structure

```
docs/dev/
├── README.md          ← this file (SSOT guide)
├── STRATEGY.md        ← strategic priorities and decision filters
├── PRD.md             ← product requirements
├── PLAN.md            ← roadmap and milestone overview
└── 0.1.0/             ← v0.1.0 milestone phase plans
    ├── phase-1-foundation-cleanup.md
    ├── phase-2-archetype-system.md
    ├── phase-3-terrain-spatial.md
    ├── phase-4-battle-memory-prompt.md
    ├── phase-5-rich-cli.md
    └── phase-6-integration-balance.md
```

### Milestone Directory Convention

Each milestone version gets its own directory (e.g., `0.1.0/`, `0.2.0/`). Phase plans within a milestone are named `phase-N-short-name.md`. Completed milestones may be archived by renaming the directory (e.g., `0.1.0-archived/`).

---

## 4. Document Responsibilities

### `STRATEGY.md`

Owns: current strategic truth, priority order, decision filters, explicit non-goals.
Does not own: full product spec, detailed roadmap phases, implementation checklists.

### `PRD.md`

Owns: durable product intent, experience requirements, scope boundaries, success criteria, product risks.
Does not own: weekly priority shuffles, detailed task sequencing, transient implementation notes.

### `PLAN.md`

Owns: roadmap phases, what is complete / active / deferred, near-term delivery framing.
Does not own: product redefinition, conflicting scope changes, strategy overrides.

### Phase TDD Plans (`0.1.0/*.md`)

Owns: phase goal, task breakdown, acceptance criteria, execution rules, self-audit protocol, writeback.
Does not own: cross-phase scope changes, product meaning shifts, strategy overrides.

---

## 5. Phase TDD Plan Structure

Every phase plan follows this closed-loop structure (per `AGENTS.md` TDD discipline):

```
§1 Phase Goal & Purpose
§2 Prerequisites & Dependencies
§3 Execution Rules (MUST DO / MUST NOT DO)
§4 Task Breakdown
§5 Acceptance Criteria (red/green conditions)
§6 Self-Audit Checklist
§7 Self-Optimization & Retry Guidance
§8 Execution Writeback (filled after completion)
§9 Next Phase Pointer
```

The writeback section (§8) is **mandatory**. After completing a phase, the executor must append a brief covering: what was done, what passed, what failed, what changed from plan, and what the next phase should know.

---

## 6. Reference Discipline

### Stable Reference Format

Use **document + section number** as the authoritative reference.

Examples:
- `STRATEGY §3`
- `PRD §5.2`
- `PLAN §4 Phase 2`
- `Phase 2 TDD §5` (within `docs/dev/0.1.0/phase-2-archetype-system.md`)

### Cross-Reference Registry

| From | To | Relationship |
|---|---|---|
| `STRATEGY §3 Priority 2` | `PRD §5` | strategy requires fair archetype system |
| `STRATEGY §3 Priority 3` | `PRD §6` | strategy requires terrain/spatial strategy |
| `STRATEGY §3 Priority 4` | `PRD §7` | strategy requires battle memory and prompt contract |
| `STRATEGY §3 Priority 5` | `PRD §4` | strategy requires spectator-readable match loop |
| `PRD §5` | `PLAN §4 Phase 2` | archetype requirements → archetype phase |
| `PRD §6` | `PLAN §4 Phase 3` | terrain requirements → terrain phase |
| `PRD §7` | `PLAN §4 Phase 4` | prompt contract requirements → prompt phase |
| `PRD §4` | `PLAN §4 Phase 5` | match loop requirements → rich CLI phase |
| `PRD §10` | `PLAN §6` | success criteria → exit criteria |

---

## 7. Change Protocol

Before changing any development SSOT doc:

1. Identify which document owns the truth you are changing.
2. Check whether the change affects a higher or lower authority doc.
3. Update dependent docs in the same change.
4. If you change section numbering, search for old `§` references and update them.
5. Re-read the docs in macro → detail order if the change is strategic rather than cosmetic.

---

## 8. For AI Executors

If you are an LLM executing a phase:

1. Read `AGENTS.md` first for repo-level instructions and commands.
2. Read the full doc chain: `STRATEGY.md` → `PRD.md` → `PLAN.md` → your phase TDD plan.
3. Do not deviate from the phase plan's scope. If you discover that the plan is wrong or incomplete, document the issue in the writeback — do not silently expand scope.
4. Run tests after every significant change. The test command is in `AGENTS.md`.
5. When the phase is complete, write the execution writeback into your phase plan before stopping.
6. Do not start the next phase. Leave that to the next invocation.

---

## 9. Lean Docs Rule

This project should not carry enterprise-grade documentation overhead.

- Prefer 3–4 strong SSOT docs + focused phase plans over 20 weak docs.
- Add a new doc only when an existing one can no longer stay readable.
- Phase plans are temporary execution artifacts. They are useful during v0.1.0 and may be archived after.

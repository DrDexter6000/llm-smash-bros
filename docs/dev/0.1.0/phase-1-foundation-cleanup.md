# Phase 1 — Foundation Cleanup

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 1`
**Prerequisites:** None (first phase)

---

## §1 Phase Goal & Purpose

Fix known bugs and mechanical debt so the codebase is **honest and stable** before new features are built on top of it.

**Why this matters:** Phase 2+ will restructure the fighter system, add terrain, and rewrite prompts. All of that work is safer and faster on a clean foundation. Specifically:

- The `__main__.py` duplicate bug means the CLI is subtly broken.
- Ability descriptions that reference unimplemented effects (stun, slow, reflection, absorb) **lie to the LLM**, causing it to make decisions based on false information. This corrupts any evaluation signal.
- Missing `.gitignore` rules risk leaking API keys if the repo goes public.

---

## §2 Prerequisites & Dependencies

- Access to `backend/` directory and the Python venv.
- Ability to run `backend\.venv\Scripts\python.exe -m pytest -q` (or `uv run pytest -q`).
- Read the full doc chain before starting: `STRATEGY.md` → `PRD.md` → `PLAN.md` → this file.

---

## §3 Execution Rules

### MUST DO

- Run the full test suite before making any changes (establish baseline).
- Fix the `__main__.py` duplicate code — keep only one argument-parsing + `asyncio.run()` path.
- Audit every ability `description` in `roster.py` against `combat.py` / `game.py`. For each ability:
  - If the described effect IS implemented in the engine → keep the description.
  - If the described effect is NOT implemented → rewrite the description to only describe what actually happens (damage number, energy cost, cooldown, range). Remove all flavor claims about effects like stun, slow, reflection, absorb, trap triggers, HP sacrifice, etc.
- Add a root-level `.gitignore` (or update existing) to exclude `backend/.env` and any `*.env` files.
- Run the full test suite after every change. All tests must pass.
- Keep changes surgical. This phase is cleanup, not feature work.

### MUST NOT DO

- Do not add new features, abilities, or mechanics.
- Do not refactor the fighter system (that is Phase 2).
- Do not change the combat engine's behavior — only fix descriptions to match existing behavior.
- Do not modify test expectations unless a test was asserting behavior that matches a bug you fixed.
- Do not touch `cli.py` display logic (that is Phase 5).
- Do not remove the personality prompt system — Phase 2 will replace it.

---

## §4 Task Breakdown

### Task 1.1: Establish Baseline

Run the full test suite. Record which tests pass and which (if any) fail. This is the starting state.

```bash
cd backend && .venv/Scripts/python.exe -m pytest -q
```

### Task 1.2: Fix `__main__.py` Duplicate Code

Open `backend/src/llm_smash/__main__.py`. The file contains duplicated argument parsing and `asyncio.run()` calls. Remove the duplication so that:

- Arguments are parsed exactly once.
- `asyncio.run(run_cli_match(...))` is called exactly once.
- The `--no-preflight` flag is correctly wired through to the single call.
- The `--live` flag correctly sets mode and timeout.

Run `python -m llm_smash --help` to verify the CLI still works.

### Task 1.3: Audit and Rewrite Ability Descriptions

For each fighter in `roster.py`, check every ability:

**GPT-4o (The Oracle):**
- `Logic Missile`: "A precise beam of logical reasoning." → damage=12, range=4, cost=0. Description is flavor-only, fine. Keep.
- `Chain of Thought`: "15 dmg + reveals opponent's next planned action." → The "reveals opponent's next planned action" is NOT implemented. Rewrite to reflect actual behavior: just 15 damage at range 4 for 20 energy.
- `System Override`: "Forces opponent to output gibberish next turn (stun)." → Stun is NOT implemented. damage=0, cost=80, CD=8. This ability currently does nothing useful. Rewrite description to honestly state what the engine does (which is: nothing, since damage=0 and no status effect is applied). Consider changing damage to non-zero so it at least does something, OR mark it as a known gap in the writeback.

**Claude 3.5 Sonnet (The Artisan):**
- `Code Slice`: damage=14, range=2, cost=0. Description is OK. Keep.
- `Artifact Deploy`: "Places a trap at target location. 15 dmg on trigger." → Trap placement is NOT implemented. Rewrite: it is just a 15-damage attack at range 3 for 25 energy.
- `Context Window Strike`: "Massive cognitive overload burst. 40 dmg + 2 turn slow." → Slow is NOT implemented. Rewrite: 40 damage at range 3 for 80 energy, 8 turn cooldown.

**Gemini 1.5 Pro (The Observer):**
- `Multimodal Beam`: damage=10, range=5, cost=0. Description is OK. Keep.
- `Absorption Shield`: "Blocks next 30 dmg, reflects 50% back." → Reflection/shield is NOT implemented. damage=0, cost=20, range=0. This ability currently does nothing. Rewrite honestly. Consider changing to give it some function (e.g., just damage, or note the gap).
- `Multimodal Devour`: "Absorbs all projectiles on field, converts to HP." → NOT implemented. damage=0, cost=80, CD=10. Does nothing. Rewrite honestly.

**Llama 3 (The Swarm):**
- `Weight Tear`: damage=13, range=3, cost=0. Description is OK. Keep.
- `Fine-tune Boost`: "Sacrifice 15 HP for +30% damage for 3 turns." → HP sacrifice and damage boost are NOT implemented. Rewrite honestly.
- `Fine-tuned Frenzy`: "Sacrifice 25 HP for +50% damage for 2 turns." → NOT implemented. Rewrite honestly.

**Important decision:** For abilities that currently do nothing (damage=0, no implemented effect), you have two options:
- Option A: Give them a simple damage value so they at least do something. This is a minimal behavior change.
- Option B: Leave them at damage=0 and rewrite the description to say "No effect — placeholder for future implementation."

**Recommended:** Option A for ultimates (give them damage so they are not completely useless), with an honest description. This keeps mock matches playable. Do not add status effects — that is Phase 2 territory.

### Task 1.4: Add Root `.gitignore`

Create or update the root `.gitignore` to include:

```
# Environment files with secrets
**/.env
!**/.env.example

# Python
__pycache__/
*.pyc
.ruff_cache/
```

Verify `backend/.env` is covered by this rule.

### Task 1.5: Final Test Suite Run

Run the full test suite. All tests must pass. If any test fails due to your description changes, update the test to match the new (honest) descriptions — but only the assertion text, not test logic.

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | `__main__.py` has no duplicate code | `asyncio.run` appears more than once | `asyncio.run` appears exactly once |
| 2 | All ability descriptions match engine behavior | Any description claims an effect not in `combat.py`/`game.py` | Every described effect has corresponding engine code |
| 3 | No ability has damage=0 with no implemented effect | An ability exists that does literally nothing when used | Every ability either deals damage, applies a real mechanic, or is explicitly documented as placeholder |
| 4 | Root `.gitignore` covers `.env` | `git status` shows `backend/.env` as trackable | `.env` files are ignored |
| 5 | All tests pass | Any test failure | `pytest -q` exits 0 |
| 6 | CLI runs without error | `python -m llm_smash` crashes or behaves unexpectedly | Mock match completes successfully |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Read `__main__.py` end-to-end. Does it have a single, clear execution path?
- [ ] Read every ability description in `roster.py`. Can you find the matching engine behavior for each claim?
- [ ] Run `git diff` and review every change. Is anything beyond cleanup scope?
- [ ] Run `python -m llm_smash` and watch a mock match complete. Does it look right?
- [ ] Run `pytest -q`. All green?

---

## §7 Self-Optimization & Retry Guidance

**If tests fail after your changes:**
- Check if the failure is in a test that asserts on ability descriptions (likely `test_roster.py`). Update the assertion to match your new description.
- Check if the failure is in a test that expected the old `__main__.py` behavior. Update accordingly.
- Do NOT change test logic to make tests pass. Only change assertion values that reference text you intentionally modified.

**If you are unsure whether an ability effect is implemented:**
- Search `combat.py` and `game.py` for the effect keyword (e.g., "stun", "reflect", "shield").
- If no code references it, the effect is not implemented.

**If you accidentally change engine behavior:**
- Revert. This phase is description-only cleanup. If you need to change combat math, stop and document the need in the writeback.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** _(executor name/model)_
**Date:** _(date)_

**What was done:**

**What passed:**

**What failed or was unexpected:**

**What changed from plan:**

**State left for Phase 2:**

---

## §9 Next Phase Pointer

**Next:** Phase 2 — Archetype System (`docs/dev/0.1.0/phase-2-archetype-system.md`)

**What Phase 2 needs from this phase:**
- A clean `__main__.py` with a single execution path.
- Honest ability descriptions that match engine behavior (Phase 2 will replace these entirely).
- A green test suite as baseline.
- Root `.gitignore` covering `.env` files.

**What Phase 2 does NOT need from this phase:**
- Any new features, abilities, or mechanics.
- Any changes to the fighter system structure (Phase 2 owns that).

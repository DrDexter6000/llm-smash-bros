# Phase 2 — Archetype System

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 2`, `PRD §5`
**Prerequisites:** Phase 1 complete (clean codebase, honest descriptions, green tests)

---

## §1 Phase Goal & Purpose

Replace the LLM-branded fighter roster with **generic, balanced archetypes** that any model can pilot. This is the single most important architectural change for the project's evaluation credibility.

**Why this matters:**
- Per `STRATEGY §2.1`, the arena must be a fair playground. Tying fighter abilities to LLM brand names conflates "model personality" with "game kit advantages."
- A mirror match (same archetype, different models) is the purest evaluation of decision quality.
- The current roster has abilities that do nothing (see Phase 1 cleanup). The new system designs every ability to have a working engine implementation.

---

## §2 Prerequisites & Dependencies

- Phase 1 complete: `__main__.py` fixed, ability descriptions honest, tests green.
- Full doc chain read: `STRATEGY.md` → `PRD.md` (especially §5) → `PLAN.md` → this file.
- Understanding of current engine: `state.py` (models), `combat.py` (damage/movement), `game.py` (turn loop), `validator.py` (response parsing).

---

## §3 Execution Rules

### MUST DO

- Design 4 archetypes per `PRD §5.2`: Striker, Guardian, Controller, Berserker.
- Each archetype gets exactly **4 abilities**: 1 basic (0 energy, 0 CD), 2 tactical (medium energy, may have CD), 1 ultimate (high energy, long CD).
- **Every ability effect must be implemented in `combat.py` / `game.py`.** If you write "applies stun for 1 turn" in a description, the stun must actually work in the engine.
- Implement status effects that abilities reference: at minimum `stun` (skip action), `slow` (cannot move), `damage_boost` (% increase to outgoing damage). The `StatusEffect` model already exists in `state.py`; the application logic in `combat.py` / `game.py` needs to be added.
- Update `roster.py` to use archetype IDs (`striker`, `guardian`, `controller`, `berserker`) instead of LLM names.
- Update `MatchConfig` and `GameEngine` to support archetype selection independently from LLM client assignment. The config should map: `{slot: {archetype: "striker", llm_client: <adapter>}}`.
- Update system prompts: `BASE_SYSTEM_PROMPT` stays as game rules; the personality section becomes **archetype identity** (role, win condition, ideal patterns).
- Update `__main__.py` and `cli.py` to use new archetype selection (default to random or configurable).
- Write tests for every new ability and status effect.
- All existing tests must still pass (or be updated to reflect the new system).

### MUST NOT DO

- Do not add terrain (Phase 3).
- Do not change the prompt output format / add turn history (Phase 4).
- Do not change CLI display logic beyond what is needed for new archetype names (Phase 5).
- Do not design more than 4 archetypes.
- Do not add abilities beyond 4 per archetype.
- Do not implement combo mechanics between abilities (keep each ability self-contained for now).

---

## §4 Task Breakdown

### Task 2.1: Design Archetype Stats and Abilities

Create the complete archetype spec before writing code. Use the constraints from `PRD §5.2`:

**Striker** (Burst / Assassin)
- HP: 80, Max Energy: 100
- Win condition: close range burst damage, high mobility
- Basic: moderate damage, short range (1-2)
- Tactical A: gap-closer or burst (medium cost)
- Tactical B: evasion or disengage utility
- Ultimate: massive single-target burst (high cost, long CD)

**Guardian** (Tank / Control)
- HP: 120, Max Energy: 80
- Win condition: outlast, absorb, punish aggression
- Basic: low damage, medium range (2-3)
- Tactical A: damage reduction buff (self-apply status effect)
- Tactical B: moderate damage + applies slow to target
- Ultimate: large AoE or high-impact control (e.g., stun)

**Controller** (Range / Zoner)
- HP: 90, Max Energy: 100
- Win condition: maintain distance, area denial, chip damage
- Basic: low-moderate damage, long range (4-5)
- Tactical A: area denial or damage at range
- Tactical B: knockback or repositioning tool
- Ultimate: high damage at range or large area effect

**Berserker** (Glass Cannon / Momentum)
- HP: 65, Max Energy: 120
- Win condition: self-buff, overwhelm before dying
- Basic: moderate damage, medium range (2-3)
- Tactical A: self-damage for damage boost (applies `damage_boost` status)
- Tactical B: reckless attack (high damage but costs HP)
- Ultimate: massive self-buff or AoE (high cost, significant self-damage)

**Output of this task:** A written spec (can be comments in code or a section in this file's writeback) with exact numbers for every ability: name, type, damage, energy_cost, cooldown, range, effect description, and status effect details.

### Task 2.2: Implement Status Effect Application

The `StatusEffect` model exists in `state.py` but effects are never applied during combat. Add implementation:

In `combat.py` or `game.py` (wherever turn resolution happens):

1. **Stun check:** Before requesting an action from a fighter, check `fighter.has_status("stun")`. If stunned, skip the LLM call entirely and auto-defend (no fumble penalty — this is a game mechanic, not a failure).
2. **Slow check:** Before resolving movement, check `fighter.has_status("slow")`. If slowed, ignore the move command (fighter stays in place).
3. **Damage boost:** In `calculate_damage()`, check `attacker.has_status("damage_boost")`. If active, multiply damage by `(1 + effect.value)` where `value` is the percentage (e.g., 0.3 for 30%).

Add a method to `CombatResolver` or `GameEngine` to **apply a status effect** to a fighter (push a `StatusEffect` onto `fighter.status_effects`). Abilities that apply status effects will call this after damage resolution.

### Task 2.3: Implement Ability Effects in Engine

For each non-basic ability across all 4 archetypes, implement the specific effect:

- Damage-only abilities: already work via existing `calculate_damage()`.
- Self-buff abilities (damage_boost, damage_reduction): apply a `StatusEffect` to the caster.
- Debuff abilities (slow, stun on target): apply a `StatusEffect` to the target after damage.
- Self-damage abilities (Berserker): reduce caster HP as part of resolution.
- Knockback abilities (Controller): move target 1-2 tiles away from caster (clamp to arena bounds).

Each effect must be triggered during the action resolution step in `game.py`'s `_execute_turn()`.

### Task 2.4: Rewrite `roster.py`

Replace the 4 LLM-branded fighters with 4 archetype definitions:

- Change `FIGHTER_IDS` to `ARCHETYPE_IDS = ["striker", "guardian", "controller", "berserker"]`.
- Replace `_create_oracle()` etc. with `_create_striker()` etc.
- Each archetype gets a `codename` that is the archetype name, not an LLM reference (e.g., codename="Striker", not "The Oracle").
- Update `get_fighter()` → `get_archetype()`, `get_all_fighters()` → `get_all_archetypes()`.
- Update all imports and references across the codebase.

### Task 2.5: Rewrite System Prompts

Update `BASE_SYSTEM_PROMPT`:
- Keep the game rules section.
- Keep the JSON format section.
- Keep the tactical tips section (update for any new mechanics like status effects).

Replace `PERSONALITY_PROMPTS` with `ARCHETYPE_PROMPTS`:
```python
ARCHETYPE_PROMPTS = {
    "striker": (
        "ARCHETYPE: Striker (Burst / Assassin)\n"
        "YOUR WIN CONDITION: Close distance, deliver burst damage, retreat to recover.\n"
        "YOUR STRENGTHS: High damage, mobility. YOUR WEAKNESSES: Low HP, short range.\n"
        "IDEAL PATTERN: Approach → burst → retreat → recover energy → repeat.\n"
        "PERSONALITY: Aggressive, confident, taunts about speed and precision."
    ),
    # ... etc for each archetype
}
```

### Task 2.6: Update Match Config and Engine Wiring

Modify `MatchConfig` and `GameEngine` to support the new model:

- `MatchConfig.fighter_ids` → `MatchConfig.archetype_ids` (list of 2 archetype IDs).
- Add `MatchConfig.fighter_labels` or similar for display names (optional, can default to archetype name).
- `GameEngine.__init__` maps `llm_clients` by slot, not by fighter ID. The client dict keys should be slot-based (e.g., `"fighter_1"`, `"fighter_2"`) or archetype-based.
- Update `cli.py` and `__main__.py` CLI arguments to accept archetype selection.

**Important:** The LLM client assignment is now separate from archetype choice. A match config might look like:
```python
MatchConfig(
    archetype_ids=["striker", "guardian"],
    max_turns=50,
)
# LLM clients are mapped separately:
# {"fighter_1": openai_client, "fighter_2": anthropic_client}
```

### Task 2.7: Update Tests

- Update `test_roster.py` for new archetype IDs and definitions.
- Add tests for status effect application (stun skips action, slow skips movement, damage_boost multiplies damage).
- Add tests for each ability's specific effect.
- Update `test_game.py` for new MatchConfig format.
- Update `test_cli.py` for new CLI arguments.
- Update `conftest.py` fixtures to use archetypes.
- Run full suite: all green.

### Task 2.8: Verify Mock Match

Run `python -m llm_smash` and confirm a mock match completes without errors using the new archetype system.

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | 4 archetypes defined | Fewer than 4, or any references LLM names | 4 archetypes with generic IDs and abilities |
| 2 | Each archetype has 4 abilities | Any archetype has != 4 abilities | All have exactly 4: basic + 2 tactical + ultimate |
| 3 | All ability effects implemented | Any ability description claims an unimplemented effect | Every described effect has engine code |
| 4 | Status effects work | Stun/slow/damage_boost described but not applied in engine | Each status type modifies combat resolution correctly |
| 5 | Model-archetype decoupled | Fighter ID implies a specific LLM | Any LLM can be assigned to any archetype |
| 6 | System prompts archetype-based | Prompts reference specific LLMs | Prompts describe archetype role and strategy |
| 7 | All tests pass | Any test failure | Full suite green |
| 8 | Mock match runs | CLI crashes or errors | Mock match completes with new archetypes |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] `grep -ri "gpt-4o\|claude-3.5\|gemini-1.5\|llama-3" backend/src/` returns zero results (no LLM brand references in source code).
- [ ] Every ability in `roster.py` — find its effect handler in `combat.py` or `game.py`.
- [ ] A stunned fighter does not get an LLM call and auto-defends.
- [ ] A slowed fighter's move command is ignored.
- [ ] A damage-boosted fighter deals extra damage.
- [ ] `MatchConfig` does not require a specific LLM to be paired with a specific archetype.
- [ ] System prompts do not mention any specific LLM model name.
- [ ] Run `python -m llm_smash` — mock match completes.
- [ ] Run `pytest -q` — all green.

---

## §7 Self-Optimization & Retry Guidance

**If archetype balance feels wrong during mock testing:**
- Do not spend time fine-tuning numbers in this phase. Document the imbalance in the writeback. Phase 6 will handle balance tuning.
- Ensure the basic math is sane: no archetype should one-shot another from full HP with a basic attack.

**If status effect implementation is complex:**
- Start with the simplest version: stun = skip turn, slow = skip move, damage_boost = multiply. No stacking, no interaction between effects.
- If stun/slow feel too powerful, set them to 1 turn duration. Tune later.

**If the MatchConfig refactor is larger than expected:**
- Keep backward compatibility in this phase if needed. The key requirement is that archetypes work; the config API can be refined later.
- Minimum viable change: fighter IDs change from LLM names to archetype names; the rest of the wiring stays similar.

**If tests are extensively broken by the refactor:**
- Prioritize fixing `conftest.py` fixtures first (they cascade to all tests).
- Then fix test files one by one: `test_roster.py` → `test_combat.py` → `test_game.py` → rest.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** Sisyphus-Junior / gpt-5.4
**Date:** 2026-04-07

**What was done:**
- Replaced the branded roster with four generic archetypes: Striker, Guardian, Controller, Berserker.
- Added `AbilityEffect` and effect-driven ability resolution for status application, self-damage, and knockback.
- Implemented `damage_boost` and `damage_reduction` in `combat.py`, plus stun/slow handling in `game.py`.
- Updated CLI/archetype wiring, prompts, tests, and migration aliases (`FIGHTER_IDS`, `get_archetype`, `get_all_archetypes`).

**What passed:**
- Targeted test files for state, roster, combat, game, CLI, validator, adapters, and live client wrappers.
- Full backend pytest suite.
- Mock CLI match via `python -m llm_smash --seed 42`.
- Source self-audit for old branded fighter/archetype names in `backend/src/`.

**What failed or was unexpected:**
- Root-level LSP diagnostics on tests still report some import-resolution noise because the package lives under `backend/src`; backend test runs stayed green, matching repo guidance.
- The phase plan suggested a bigger `MatchConfig` refactor, but the lighter migration path was sufficient: `fighter_ids` now carry archetype IDs while live client mapping remains keyed by those IDs.

**Archetype stats finalized (record exact numbers here):**
- **Striker** — HP 80, Energy 100: Quick Strike (12 dmg, r2, cost 0, cd 0), Blitz Rush (18 dmg, r3, cost 20, cd 0), Evasive Maneuver (0 dmg, self `damage_reduction` 0.3 for 1 turn, cost 15, cd 2), Execution (40 dmg, r2, cost 80, cd 8).
- **Guardian** — HP 120, Energy 80: Shield Bash (10 dmg, r2, cost 0, cd 0), Fortify (0 dmg, self `damage_reduction` 0.4 for 2 turns, cost 20, cd 3), Punishing Strike (14 dmg, r2, cost 25, cd 0, applies `slow` for 1 turn), Earthshatter (25 dmg, r4, cost 70, cd 8, applies `stun` for 1 turn).
- **Controller** — HP 90, Energy 100: Signal Beam (10 dmg, r5, cost 0, cd 0), Area Denial (12 dmg, r4, cost 20, cd 0), Repulsor (8 dmg, r3, cost 25, cd 2, knockback 2), Overwhelming Force (35 dmg, r5, cost 80, cd 10).
- **Berserker** — HP 65, Energy 120: Wild Swing (14 dmg, r2, cost 0, cd 0), Bloodlust (0 dmg, self-damage 10, self `damage_boost` 0.4 for 2 turns, cost 15, cd 3), Reckless Assault (22 dmg, r2, self-damage 8, cost 25, cd 0), Unleashed Fury (45 dmg, r2, self-damage 15, cost 80, cd 8).

**What changed from plan:**
- Kept `MatchConfig.fighter_ids` for compatibility instead of renaming to `archetype_ids`.
- Preserved backward-compatible helper names (`get_fighter`, `get_all_fighters`, `FIGHTER_IDS`) while making them archetype-backed.
- Tightened default OpenAI client example text/model away from old branded roster naming to keep source self-audit clean.

**State left for Phase 3:**
- Archetypes are now mechanically honest and decoupled from model identity.
- Status effects needed by Phase 2 are implemented and covered by tests.
- Engine still uses a flat arena with no terrain logic yet, so Phase 3 can layer spatial systems on top of a stable archetype baseline.

---

## §9 Next Phase Pointer

**Next:** Phase 3 — Terrain & Spatial Strategy (`docs/dev/0.1.0/phase-3-terrain-spatial.md`)

**What Phase 3 needs from this phase:**
- 4 working archetypes with all abilities implemented.
- Status effects (stun, slow, damage_boost) working in engine.
- Updated `MatchConfig` with archetype-based setup.
- Green test suite.

**What Phase 3 does NOT need from this phase:**
- Perfect archetype balance (Phase 6 handles that).
- Terrain-related mechanics (Phase 3 adds those).
- Prompt format changes (Phase 4 handles that).

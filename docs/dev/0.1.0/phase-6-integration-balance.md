# Phase 6 — Integration, Balance & Verification

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 6`, `PRD §10`
**Prerequisites:** Phase 5 complete (rich CLI, replay serialization, all features integrated)

---

## §1 Phase Goal & Purpose

Prove that the system works **end-to-end** and that matches are **credible evaluation instruments**. This phase produces evidence, not features. It answers: "Does the game actually showcase model differences fairly?"

**Why this matters:**
- Without integration tests, we have unit-tested components that might not work together.
- Without balance analysis, we don't know if archetype design or random variance dominates outcomes.
- Without fumble rate measurement, we can't claim matches are "real" rather than "mostly fallbacks."
- Per `PRD §10`, this phase verifies all v0.1.0 exit criteria before the milestone is declared complete.

---

## §2 Prerequisites & Dependencies

- Phase 5 complete: rich CLI, replay serialization, all game features working, green unit tests.
- Understanding of: `game.py` (match lifecycle), `MatchResult` / `TurnLog` (data structures), replay JSON format.
- Access to live LLM APIs if verifying live matches (not required for mock-based integration tests).

---

## §3 Execution Rules

### MUST DO

- Write **integration tests** that run full mock matches end-to-end (GameEngine → adapters → combat → display).
- Build a **batch match runner** that executes N matches with different seeds and collects statistics.
- Measure and report:
  - Per-archetype win rates (all 6 matchup combinations + mirror matches).
  - Per-match fumble rate.
  - Average match length (turns).
  - Randomness impact: run the same matchup 20 times with different seeds, measure win rate variance.
- Verify all `PLAN §6` exit criteria with evidence.
- Write the analysis results into the execution writeback.
- All tests pass.

### MUST NOT DO

- Do not add new features.
- Do not tune archetype stats based on mock-mode results (mock adapter is randomized, not a real model).
- Do not change game mechanics to fix balance. Only document findings.
- Do not block the milestone on perfect balance — document the current state and recommend Phase 2 tune-ups for the next milestone if needed.

---

## §4 Task Breakdown

### Task 6.1: Write Integration Tests

Create `backend/tests/test_integration.py`:

```python
async def test_full_mock_match_completes():
    """A full mock match runs to completion without errors."""
    # Setup MatchConfig with 2 archetypes, mock LLM clients
    # Run GameEngine.run_match()
    # Assert: result is MatchResult, has winner or is_draw, total_turns > 0

async def test_full_mock_match_produces_valid_turn_logs():
    """Each turn log has valid structure."""
    # Run a match
    # For each TurnLog: assert turn_number, actions dict, events list
    # Assert tactical_summary and trash_talk fields in actions

async def test_full_mock_match_with_terrain():
    """Terrain is generated and appears in the match."""
    # Run a match with a seed that generates terrain
    # Assert arena has terrain tiles
    # Assert at least one terrain-related event (fighter on HG, on Cover, blocked by Rift)

async def test_all_archetype_matchups_complete():
    """All 6 pairwise matchups + 4 mirrors complete without errors."""
    # 10 total matchups
    # Each runs a short match (max_turns=20)
    # Assert all complete

async def test_replay_serialization_roundtrip():
    """Match result serializes to JSON and deserializes back."""
    # Run a match, serialize to JSON, deserialize, compare key fields

async def test_fumble_handling_in_match():
    """A match with high fumble rate still completes."""
    # Use a mock client with high failure_rate
    # Assert match completes, fumble count > 0
```

### Task 6.2: Build Batch Match Runner

Create `backend/src/llm_smash/tools/batch_runner.py` (or a script in `backend/scripts/`):

```python
async def run_batch(
    archetype_a: str,
    archetype_b: str,
    num_matches: int = 20,
    max_turns: int = 50,
) -> BatchResult:
    """Run N mock matches and collect statistics."""

@dataclass
class BatchResult:
    matchup: str  # e.g., "striker_vs_guardian"
    total_matches: int
    wins_a: int
    wins_b: int
    draws: int
    avg_turns: float
    avg_fumbles: float
    win_rate_a: float
    win_rate_b: float
```

Add a CLI command: `python -m llm_smash --batch --matches 20` that runs all matchup combinations and prints a summary table.

### Task 6.3: Run Archetype Balance Analysis

Execute the batch runner for all matchups (mock mode):

**Matchup matrix (6 cross + 4 mirror = 10 total):**
- Striker vs Guardian (20 matches)
- Striker vs Controller (20 matches)
- Striker vs Berserker (20 matches)
- Guardian vs Controller (20 matches)
- Guardian vs Berserker (20 matches)
- Controller vs Berserker (20 matches)
- Striker mirror (20 matches)
- Guardian mirror (20 matches)
- Controller mirror (20 matches)
- Berserker mirror (20 matches)

Record results in the writeback table.

**Important caveat:** Mock mode uses a randomized adapter, not real LLM decision-making. This measures engine balance and randomness, not model evaluation quality. Real model balance requires live testing in a future milestone.

### Task 6.4: Measure Fumble Rates

From the batch results, extract:
- Average fumble rate per match.
- Do any archetypes have systematically higher fumble rates? (They shouldn't in mock mode, but verify.)

### Task 6.5: Measure Randomness Impact

For one matchup (e.g., Striker vs Guardian), run 20 matches with different seeds:
- Calculate win rate for archetype A.
- If the win rate is close to 50/50 (40-60%), randomness is dominant over archetype design in mock mode. This is expected but should be documented.
- If one archetype wins >70%, there may be a balance issue in the game mechanics.

### Task 6.6: Verify v0.1.0 Exit Criteria

Go through `PLAN §6` checklist item by item:

| Exit Criterion | How to Verify | Evidence |
|---------------|---------------|----------|
| Archetypes generic and decoupled | `grep` for LLM names in source | Zero results |
| Terrain creates positioning decisions | Review terrain integration test | Test passes, terrain events in logs |
| Models receive turn history | Inspect perspective JSON | `recent_turns` present |
| Models produce tactical summaries | Inspect turn logs | `tactical_summary` populated |
| Terminal output OBS-ready | Visual inspection of `rich` CLI | Screenshot or description |
| All abilities implemented | Audit roster vs engine | No unimplemented effects |
| Matches feel skill-driven | Batch analysis | Win rates documented |
| Mirror matches showcase differences | Run mirrors, inspect | Documented observation |
| All tests pass | `pytest -q` | Exit code 0 |

### Task 6.7: Write Final Verification Report

Append a comprehensive report to the writeback section. This report is the evidence that v0.1.0 is ready.

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Integration tests exist | No integration test file | ≥5 integration tests, all passing |
| 2 | Batch runner works | No batch runner or crashes | Runs 20 matches per matchup, outputs stats |
| 3 | All matchups complete | Any matchup crashes | All 10 matchup combinations complete |
| 4 | Balance documented | No balance data | Win rate table for all matchups in writeback |
| 5 | Fumble rate documented | No fumble data | Average fumble rate per match documented |
| 6 | Exit criteria verified | Any exit criterion unverified | All 9 criteria checked with evidence |
| 7 | All tests pass | Any failure | Full suite green including integration tests |

---

## §6 Self-Audit Checklist

- [ ] All integration tests pass independently (not order-dependent).
- [ ] Batch runner produces consistent results across runs (given same seeds).
- [ ] Balance analysis is recorded in writeback with actual numbers.
- [ ] Exit criteria checklist is complete with evidence for each item.
- [ ] No new features were added (this phase is measurement only).
- [ ] `pytest -q` — all green.

---

## §7 Self-Optimization & Retry Guidance

**If integration tests are flaky:**
- Use fixed seeds for deterministic matches. Flaky tests in a seeded-RNG system indicate a real bug.
- Check for shared state between tests (module-level variables, singleton patterns).

**If balance is wildly off:**
- Document it. Do not fix it in this phase.
- Note which archetype seems overpowered and hypothesize why (e.g., "Guardian's damage reduction stacks too well with Cover terrain").
- Recommend specific tuning for a follow-up.

**If the batch runner is too slow:**
- Mock mode should be fast (no API calls). If slow, check for unnecessary `asyncio.sleep()` or file I/O.
- 200 total matches (10 matchups × 20) should complete in under 30 seconds in mock mode.

**If exit criteria can't be fully verified in mock mode:**
- That's OK. Mark live-mode criteria as "verified in mock, requires live confirmation." This is honest and expected.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** _(executor name/model)_
**Date:** _(date)_

**What was done:**

**Integration test results:**

**Archetype balance matrix (mock mode, 20 matches each):**

| Matchup | A Wins | B Wins | Draws | A Win% | Avg Turns | Avg Fumbles |
|---------|--------|--------|-------|--------|-----------|-------------|
| Striker vs Guardian | | | | | | |
| Striker vs Controller | | | | | | |
| Striker vs Berserker | | | | | | |
| Guardian vs Controller | | | | | | |
| Guardian vs Berserker | | | | | | |
| Controller vs Berserker | | | | | | |
| Striker mirror | | | | | | |
| Guardian mirror | | | | | | |
| Controller mirror | | | | | | |
| Berserker mirror | | | | | | |

**Fumble rate analysis:**

**Randomness analysis (single matchup, 20 runs):**

**v0.1.0 exit criteria verification:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Archetypes decoupled | | |
| Terrain positioning | | |
| Turn history | | |
| Tactical summaries | | |
| OBS-ready terminal | | |
| All abilities implemented | | |
| Skill-driven outcomes | | |
| Mirror match value | | |
| All tests pass | | |

**What failed or was unexpected:**

**What changed from plan:**

**Recommendations for v0.2.0:**

---

## §9 Next Phase Pointer

**Next:** v0.1.0 milestone is complete after this phase.

**Post-milestone actions:**
1. Update `PLAN.md` to mark v0.1.0 as complete.
2. Review writeback data to inform v0.2.0 planning.
3. Consider running batch analysis with real LLMs (live mode) to validate evaluation credibility.
4. Begin v0.2.0 planning (Web Spectator Layer) per `PLAN §5`.

**What the next milestone needs:**
- Stable archetype system with documented balance characteristics.
- Replay JSON format as the data contract for a web replay viewer.
- Rich CLI as the reference implementation for the spectator experience.
- All documentation updated to reflect v0.1.0 reality.

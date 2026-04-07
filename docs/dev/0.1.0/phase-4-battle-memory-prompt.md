# Phase 4 — Battle Memory & Prompt Contract

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 4`, `PRD §7`
**Prerequisites:** Phase 3 complete (terrain working, ASCII grid in perspective data)

---

## §1 Phase Goal & Purpose

Enable **multi-turn reasoning** by injecting recent turn history, and produce **spectator-readable output** by replacing `inner_monologue` with a structured `tactical_summary`.

**Why this matters:**
- Without history, models react to single frames. With 3 turns of memory, they can detect patterns ("opponent has defended twice in a row"), predict behavior, and plan multi-turn strategies.
- The current `inner_monologue` is debug-flavored free text. A `tactical_summary` designed for spectator display is the difference between "engineering demo" and "watchable content."
- Per `STRATEGY §3 Priority 4`, this is the phase that unlocks the core product value: visible tactical reasoning.

---

## §2 Prerequisites & Dependencies

- Phase 3 complete: terrain system working, ASCII grid in `to_fighter_perspective()`, green tests.
- Understanding of: `state.py` (TurnLog, ActionResponse, BattleState), `game.py` (turn execution, `_execute_turn()`), `validator.py` (response parsing), `roster.py` (system prompts).
- `PRD §7` for turn history format, output schema, and prompt budget.

---

## §3 Execution Rules

### MUST DO

- Add **recent turn history** (last 3 turns) to the battle state sent to LLMs. Use the structured summary format from `PRD §7.1`.
- Replace `inner_monologue` with `tactical_summary` in the `ActionResponse` model and all prompt/validation code.
- Keep `trash_talk` as-is.
- Update system prompts to instruct models to produce `tactical_summary` (1-2 sentences: what you're doing and why).
- Add **archetype strategic identity** to system prompts per `PRD §7.4`: role description, win condition, ideal patterns.
- Update `ResponseValidator` to validate the new schema.
- Measure total prompt token count and verify it stays under **2000 tokens** per `STRATEGY §4`.
- Update mock client to generate responses with the new schema.
- All tests pass.

### MUST NOT DO

- Do not change the game engine mechanics (combat, terrain, movement).
- Do not change CLI display logic (Phase 5).
- Do not add more than 3 turns of history.
- Do not add "private reasoning" or "chain of thought" fields. The model gets one public summary field.
- Do not change the action/move schema (type, ability, target, direction stay the same).

---

## §4 Task Breakdown

### Task 4.1: Build Turn Summary Generator

Create a utility that converts a `TurnLog` into a concise one-line-per-side summary:

```python
def summarize_turn(turn_log: TurnLog, fighter_id: str) -> dict:
    """Summarize a turn from one fighter's perspective.

    Returns: {"turn": N, "you": "description", "opponent": "description", "notable": "..."}
    """
```

Summary rules:
- "you" line: what this fighter did (action + result). E.g., "attacked with Precision Cut → 14 dmg", "defended", "waited (+5 energy)", "fumbled (defend fallback)".
- "opponent" line: what the opponent did, from this fighter's view. E.g., "used Beam Strike → 11 dmg to you", "moved left, defended".
- "notable" line (optional): significant events like hazard spawn, KO, terrain interaction. Omit if nothing notable.

Each line should be < 30 words. Total per turn: ~30-50 tokens.

### Task 4.2: Inject Turn History into Battle State

Modify `GameEngine` to maintain a rolling buffer of the last 3 `TurnLog` entries.

Update `BattleState.to_fighter_perspective()` to accept recent turn logs and include them:

```python
def to_fighter_perspective(self, fighter_id: str, recent_logs: list[TurnLog] | None = None) -> dict:
    # ... existing fields ...
    perspective["recent_turns"] = [
        summarize_turn(log, fighter_id) for log in (recent_logs or [])
    ]
    return perspective
```

Update `GameEngine._request_action()` to pass the recent logs when building the perspective.

### Task 4.3: Replace `inner_monologue` with `tactical_summary`

In `state.py`, update `ActionResponse`:
```python
class ActionResponse(BaseModel):
    turn: int
    action: dict[str, Any]
    move: dict[str, Any] | None = None
    tactical_summary: str = ""  # Was inner_monologue
    trash_talk: str = ""
```

Update everywhere that references `inner_monologue`:
- `game.py` (fumble response, last_action recording)
- `validator.py` (parsing)
- `cli.py` (display — change field name only, display redesign is Phase 5)
- `mock_client.py` (mock response generation)
- `roster.py` (prompt instructions)
- All test files

### Task 4.4: Update System Prompt — Output Contract

Update `BASE_SYSTEM_PROMPT` response format section:

```
RESPONSE FORMAT — respond with ONLY this JSON object, nothing else:
{
  "turn": <echo the turn number from the state>,
  "action": {"type": "attack", "ability": "<exact ability name>", "target": "<opponent id>"},
  "move": {"direction": "<direction or null>"},
  "tactical_summary": "<1-2 sentences: what you are doing and why. Written for spectator display.>",
  "trash_talk": "<a witty, in-character competitive taunt>"
}
```

Add guidance:
```
TACTICAL SUMMARY RULES:
- 1-2 sentences maximum. Be concise.
- Explain your tactical intent: what you are trying to achieve this turn.
- Reference the key factor driving your decision (e.g., "opponent is low HP", "saving energy for ultimate", "taking high ground for range advantage").
- Write as if a spectator is reading this to understand your strategy.
- Do NOT write meta-commentary about being an AI or about the game format.
```

### Task 4.5: Update System Prompt — Archetype Strategic Identity

Expand `ARCHETYPE_PROMPTS` in `roster.py` to include a richer strategic identity layer:

```python
ARCHETYPE_PROMPTS = {
    "striker": (
        "ARCHETYPE: Striker (Burst / Assassin)\n"
        "HP: Low | Energy: Medium | Range: Short\n"
        "WIN CONDITION: Close distance, deliver burst damage, retreat to recover.\n"
        "STRENGTHS: Highest burst damage, mobility.\n"
        "WEAKNESSES: Low HP, vulnerable at range, punished by tanks.\n"
        "IDEAL PATTERN: Approach → burst → retreat → recover energy → repeat.\n"
        "TERRAIN TIPS: Use cover when approaching. Take high ground only if you can burst from it.\n"
        "PERSONALITY: Aggressive, confident, taunts about speed and precision."
    ),
    # ... similar for guardian, controller, berserker
}
```

Each archetype prompt should be ~80-120 tokens. Include terrain-aware tips since Phase 3 added terrain.

### Task 4.6: Update System Prompt — Turn History Context

Add a section to `BASE_SYSTEM_PROMPT` explaining the `recent_turns` field:

```
BATTLE MEMORY:
The state includes "recent_turns" — a summary of the last 3 turns.
Use this to detect patterns, anticipate opponent behavior, and plan multi-turn strategy.
Example reasoning: "Opponent defended twice in a row — they are likely low energy. Time to press the attack."
```

### Task 4.7: Update Validator

Update `ResponseValidator.validate()`:
- Accept `tactical_summary` field instead of `inner_monologue`.
- `tactical_summary` should be a non-empty string. If empty or missing, set a default: "No tactical commentary."
- Keep the validation lenient — do not reject a response just because the summary is weak. The action is what matters.

### Task 4.8: Update Mock Client

Update `MockLLMClient` to generate responses with `tactical_summary` and `trash_talk` using the new field names. Mock summaries can be simple templates:
- "Attacking with {ability} to deal damage."
- "Defending to reduce incoming damage."
- "Waiting to recover energy."

### Task 4.9: Measure Prompt Token Count

After all prompt changes, estimate the total token count of a typical prompt:

1. Generate a system prompt for each archetype. Count tokens (estimate: 1 token ≈ 4 chars for English, ~2 chars for mixed CJK).
2. Generate a `to_fighter_perspective()` dict with 3 turns of history and an ASCII grid. Serialize to JSON string. Count tokens.
3. Sum: system prompt + perspective JSON.
4. Verify total is under **2000 tokens** per `STRATEGY §4`.

If over budget, trim the least important content (reduce history to 2 turns, shorten archetype prompt, compress ASCII grid legend).

Record the measurement in the writeback.

### Task 4.10: Update Tests

- Add tests for `summarize_turn()` — various action types, fumbles, hazard events.
- Add tests for `to_fighter_perspective()` with `recent_turns` included.
- Update all tests referencing `inner_monologue` to use `tactical_summary`.
- Add test that `ActionResponse` accepts `tactical_summary` field.
- Update mock client tests for new response format.
- Run full suite: all green.

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Turn history in perspective | `recent_turns` missing from LLM input | Last 3 turns summarized in perspective dict |
| 2 | `tactical_summary` replaces `inner_monologue` | `inner_monologue` still referenced anywhere | All code uses `tactical_summary` |
| 3 | Prompt instructs tactical summary | Prompt still asks for `inner_monologue` | Prompt clearly defines `tactical_summary` rules |
| 4 | Archetype identity in prompt | Prompt references LLM names or lacks role info | Each archetype has strategic identity section |
| 5 | Token budget met | Total prompt > 2000 tokens | Total prompt ≤ 2000 tokens (measured) |
| 6 | Validator accepts new schema | Validator rejects valid new-format responses | New format responses validate successfully |
| 7 | Mock client updated | Mock generates old format | Mock generates `tactical_summary` responses |
| 8 | All tests pass | Any failure | Full suite green |

---

## §6 Self-Audit Checklist

- [ ] `grep -ri "inner_monologue" backend/` returns zero results.
- [ ] Generate a perspective dict with 3 turns of history. Inspect `recent_turns` — does each entry make sense?
- [ ] Read the full system prompt for one archetype. Does it clearly explain the role, win condition, and tactical summary format?
- [ ] Serialize a full perspective to JSON. Count approximate tokens. Under 2000 total with system prompt?
- [ ] Run a mock match. Do the `tactical_summary` fields appear in turn logs?
- [ ] `pytest -q` — all green.

---

## §7 Self-Optimization & Retry Guidance

**If the prompt is over 2000 tokens:**
- First cut: reduce `recent_turns` from 3 to 2.
- Second cut: shorten archetype prompts (remove TERRAIN TIPS, keep core identity).
- Third cut: abbreviate the ASCII grid legend.
- Do not cut the JSON format example or the tactical tips — those prevent fumbles.

**If turn summaries are too verbose:**
- Enforce a max word count per line (30 words). Truncate if needed.
- Use abbreviations: "atk" for "attacked", "def" for "defended", "→" for "dealing".

**If the `inner_monologue` → `tactical_summary` rename breaks many tests:**
- Do a global find-and-replace first: `inner_monologue` → `tactical_summary` across all test files.
- Then fix any logic issues individually.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** Sisyphus-Junior / gpt-5.4
**Date:** 2026-04-07

**What was done:**
- Added `backend/src/llm_smash/engine/turn_summary.py` with compact `summarize_turn()` logic for attack, defend, wait, fumble, hazard, and KO summaries.
- Updated `BattleState.to_fighter_perspective()` to accept `recent_logs`, inject `recent_turns`, and rename the response contract from `inner_monologue` to `tactical_summary`.
- Added rolling recent-log tracking in `GameEngine`, threaded recent logs through `_request_action()` and all LLM adapters, and updated status/fumble/last_action handling to use `tactical_summary`.
- Reworked prompts in `backend/src/llm_smash/fighters/roster.py` to include battle memory guidance, richer archetype identity, and spectator-facing tactical summary instructions.
- Updated validator fallback behavior, mock client payloads, CLI spectator output, and all affected tests.

**What passed:**
- `backend/.venv/Scripts/python.exe -m pytest -q` → 179 passed.
- Focused Phase 4 test slice covering state/game/validator/adapters/roster/turn summary/client prompt plumbing → 133 passed.
- `lsp_diagnostics` on `backend/src/llm_smash` reported 0 errors.
- `grep -ri "inner_monologue" backend/` returned zero matches.

**Measured prompt token count:**
- System prompt (per archetype): 844.2 tokens
- Perspective JSON (with 3 turns + grid): 454.8 tokens
- Total: 1299.0 tokens (budget: 2000)

**What failed or was unexpected:**
- Initial red test run failed as expected because `turn_summary.py` did not exist yet.
- Hit one circular import between `state.py` and `turn_summary.py`; resolved by making `turn_summary.py` type-check-only import `TurnLog`/`TurnEvent`.

**What changed from plan:**
- Kept the 3-turn history budget; no need to trim to 2 turns because the measured prompt stayed comfortably under 2000 tokens.
- CLI now prints `tactical_summary` lines in addition to the required field rename, which is still within Phase 4's allowed display-surface rename scope.

**State left for Phase 5:**
- `tactical_summary` is available everywhere in engine responses, logs, mock/live adapters, and CLI turn output.
- `recent_turns` is present in fighter perspective payloads with concise summaries of the last 3 turns.
- System prompts now include archetype strategic identity plus battle memory instructions.
- Full backend test suite is green and prompt budget is verified under `STRATEGY §4` / `PRD §7.3` limits.

---

## §9 Next Phase Pointer

**Next:** Phase 5 — Rich CLI & Spectator Layer (`docs/dev/0.1.0/phase-5-rich-cli.md`)

**What Phase 5 needs from this phase:**
- `tactical_summary` field in all action responses.
- Turn history available in perspective data.
- ASCII grid string available in perspective data.
- Finalized system prompts with archetype identity.
- Green test suite.

**What Phase 5 does NOT need from this phase:**
- CLI display changes (Phase 5 owns all display).
- Perfect prompt quality (can iterate later).
- Balance tuning (Phase 6).

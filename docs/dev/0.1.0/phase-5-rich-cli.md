# Phase 5 — Rich CLI & Spectator Layer

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 5`, `PRD §4`
**Prerequisites:** Phase 4 complete (tactical_summary, turn history, ASCII grid, archetype prompts)

---

## §1 Phase Goal & Purpose

Transform the terminal output into a **polished, OBS-streamable spectator experience** using the `rich` library. This is the fastest path to audience validation — before building a web GUI, a beautiful terminal with the right aesthetic is already content.

**Why this matters:**
- Per `STRATEGY §3 Priority 5`, the terminal output should be streamable via OBS.
- The current `cli.py` uses raw ANSI codes that have Windows compatibility issues.
- The `rich` library solves cross-platform rendering, provides panels/tables/progress bars, and delivers a "hacker aesthetic" that is itself a visual style.
- Adding match replay export (JSON) enables content creation, batch analysis, and future replay viewers.

---

## §2 Prerequisites & Dependencies

- Phase 4 complete: `tactical_summary` in responses, `recent_turns` in perspective, ASCII grid, green tests.
- `rich` library installed. Check `backend/pyproject.toml` — if not present, add `rich>=13.0` to dependencies.
- Understanding of: `cli.py` (current display logic), `state.py` (TurnLog, MatchResult), `game.py` (event_callback).

---

## §3 Execution Rules

### MUST DO

- Replace all raw ANSI code display in `cli.py` with `rich` equivalents.
- Implement a **panel-based battle display** showing:
  - Arena grid (ASCII terrain + fighter positions + hazards)
  - Fighter status bars (HP bar, energy bar, status effects, position, terrain)
  - Turn action summary (who did what)
  - `tactical_summary` from each fighter
  - `trash_talk` from each fighter
  - Fumble comedy display (raw gibberish from invalid responses)
- Implement **match replay serialization**: save the complete match (MatchResult with full TurnLog) to a JSON file after each match.
- Remove the `safe_print()` workaround and any Windows ANSI fallback code — `rich` handles this.
- Add a `--replay-dir` CLI flag to specify where replays are saved (default: `backend/replays/`).
- Keep the existing `--live`, `--no-preflight`, `--timeout` flags working.
- All tests pass.

### MUST NOT DO

- Do not build a web GUI or WebSocket server.
- Do not add TTS or audio.
- Do not change game engine logic.
- Do not change the prompt contract or battle state.
- Do not add interactive user input during matches (this is spectator-only).
- Do not add `rich` as a dependency to the core engine — only `cli.py` should import it.

---

## §4 Task Breakdown

### Task 5.1: Add `rich` Dependency

Check `backend/pyproject.toml` for `rich`. If missing, add `rich>=13.0` to the dependencies list. Run `uv sync` or `pip install -e .` to install.

### Task 5.2: Design Display Layout

Plan the visual layout before coding. Target layout for each turn:

```
╔═══════════════════ TURN 12 ═══════════════════╗
║                                                ║
║  Arena (8x6):                                  ║
║    01234567                                    ║
║  0 ........                                    ║
║  1 ..H..C..                                    ║
║  2 .##..##.                                    ║
║  3 A......B                                    ║
║  4 ..C..H..                                    ║
║  5 ........                                    ║
║                                                ║
╠════════════════════════════════════════════════╣
║  [STRIKER] piloted by GPT-4o                   ║
║  HP: ████████░░ 64/80   Energy: ██████░░ 60/100║
║  Position: (1,3) [High Ground]                 ║
║  Status: damage_boost (2 turns)                ║
║  Action: Precision Cut → 18 dmg to opponent    ║
║  Strategy: "Opponent low HP, pressing the kill"║
║  Trash: "Your weights need retraining."        ║
╠════════════════════════════════════════════════╣
║  [GUARDIAN] piloted by Claude 3.5 Sonnet       ║
║  HP: ██████████ 98/120  Energy: ████░░░░ 40/80 ║
║  Position: (6,3) [Cover]                       ║
║  Status: none                                  ║
║  Action: Defended (+20% reduction)             ║
║  Strategy: "Absorbing burst, waiting for CD"   ║
║  Trash: "I've processed bigger batches."       ║
╚════════════════════════════════════════════════╝
```

This is a guideline. Adapt to what `rich` panels/tables support best.

### Task 5.3: Implement Rich Display Module

Refactor `cli.py`. Create display functions using `rich`:

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress_bar import ProgressBar

console = Console()

def display_turn(turn_log: TurnLog, state: BattleState, archetype_labels: dict):
    """Display a complete turn using rich panels."""

def display_fighter_panel(fighter: Fighter, action: ActionResponse | None, archetype: str, model_name: str, arena: Arena) -> Panel:
    """Create a rich panel for one fighter's status."""

def display_arena_grid(arena: Arena, fighters: list[Fighter]) -> str:
    """Render the ASCII arena grid with rich syntax highlighting."""

def display_match_result(result: MatchResult) -> None:
    """Display the final match result screen."""

def display_fumble(fighter_codename: str, raw_output: str | None) -> None:
    """Display a fumble event with comedy gibberish."""
```

### Task 5.4: Implement HP/Energy Bars

Use `rich` progress bars or custom block characters for HP and energy display:

```python
def hp_bar(current: int, maximum: int, width: int = 20) -> Text:
    """Render an HP bar with color gradient (green → yellow → red)."""
    ratio = current / maximum if maximum > 0 else 0
    filled = int(ratio * width)
    if ratio > 0.6:
        color = "green"
    elif ratio > 0.3:
        color = "yellow"
    else:
        color = "red"
    bar = "█" * filled + "░" * (width - filled)
    return Text(f"{bar} {current}/{maximum}", style=color)
```

### Task 5.5: Implement Fumble Comedy Display

When a fighter fumbles, display the event with style:

- Show a "FUMBLE" header in red/flashing.
- If raw invalid output is available, show a truncated snippet (max 100 chars) as "cognitive breakdown gibberish."
- Show the HP penalty.

To access raw output in fumble events, the `TurnLog` or `TurnEvent` may need a `raw_output` field. Check if `AdapterResult.raw_response` is available in the turn log; if not, pipe it through.

### Task 5.6: Implement Match Replay Serialization

After a match completes, serialize the `MatchResult` to JSON:

```python
import json
from pathlib import Path

def save_replay(result: MatchResult, replay_dir: Path) -> Path:
    """Save match result as a JSON replay file."""
    replay_dir.mkdir(parents=True, exist_ok=True)
    filename = f"match_{result.match_id[:8]}_{result.total_turns}turns.json"
    path = replay_dir / filename
    path.write_text(result.model_dump_json(indent=2))
    return path
```

Add `--replay-dir` CLI argument. Default: `backend/replays/`. Add `replays/` to `.gitignore`.

### Task 5.7: Update Match Flow in CLI

Refactor `run_cli_match()` to use the new rich display:

1. Show match intro panel (archetypes, models, arena seed).
2. For each turn (via `event_callback`): call `display_turn()`.
3. After match: call `display_match_result()`.
4. After match: call `save_replay()`.

### Task 5.8: Remove Legacy ANSI Code

Delete or replace:
- `safe_print()` function and its Windows workarounds.
- All raw `\033[` ANSI escape sequences.
- Any `colorama` imports if present.

### Task 5.9: Add Archetype + Model Labels

The display needs to show both the archetype and the model piloting it. The match config or CLI must pass this info through.

In the display: `[STRIKER] piloted by GPT-4o` or `[GUARDIAN] piloted by Claude 3.5`.

The model name comes from the CLI args or env config, not from the archetype. Update CLI to accept/display model labels.

### Task 5.10: Write Tests

- Test `save_replay()`: verify JSON output is valid and loadable.
- Test that `MatchResult.model_dump_json()` produces valid JSON with all turn logs.
- Update `test_cli.py` for new CLI arguments.
- Do NOT test rich rendering output (it is visual and platform-dependent). Test the data flow, not the display.
- Run full suite: all green.

### Task 5.11: Visual Verification

Run `python -m llm_smash` and visually inspect:
- Arena grid displays correctly with terrain symbols.
- HP/energy bars render with colors.
- Fighter panels show archetype, position, terrain, action, tactical summary, trash talk.
- Fumbles display with comedy flair.
- Match result screen shows winner, total turns, total fumbles.
- Replay file is saved to `backend/replays/`.

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | `rich` used for all display | Raw ANSI codes still present | All display uses `rich` |
| 2 | Arena grid displayed | No grid in terminal output | Terrain grid visible each turn |
| 3 | Fighter panels complete | Missing HP, energy, action, or summary | All fields shown per fighter |
| 4 | Fumble comedy | Fumbles show as boring error text | Fumbles show with comedy flair and optional gibberish |
| 5 | Match replay saved | No replay file after match | JSON file saved to replay directory |
| 6 | Replay is valid JSON | Replay file fails `json.load()` | Replay loads and contains full turn logs |
| 7 | No legacy ANSI code | `\033[` found in source | Zero raw ANSI escapes in `cli.py` |
| 8 | CLI flags work | `--live`, `--replay-dir` broken | All CLI flags functional |
| 9 | All tests pass | Any failure | Full suite green |

---

## §6 Self-Audit Checklist

- [ ] `grep -r "\\\\033\[" backend/src/` returns zero results (no raw ANSI).
- [ ] `grep -r "safe_print" backend/src/` returns zero results.
- [ ] Run `python -m llm_smash` — watch a full mock match. Is it visually clear and appealing?
- [ ] Check that the replay JSON file exists and is valid.
- [ ] Run `python -m llm_smash --help` — all flags documented.
- [ ] `pytest -q` — all green.

---

## §7 Self-Optimization & Retry Guidance

**If `rich` panels don't render well on Windows:**
- Ensure `rich` is >= 13.0 (good Windows terminal support).
- Test in Windows Terminal (not cmd.exe). If cmd.exe is required, `rich` auto-detects and degrades gracefully.

**If the display is too cluttered:**
- Reduce information density per turn. Show only: grid, HP/energy bars, action, tactical summary, trash talk. Skip position coordinates and status effects from the main panel; put them in a compact line.

**If replay files are too large:**
- `state_after` in each `TurnLog` contains the full serialized state, which is verbose. Consider omitting it from replay files or making it optional.

**If fumble raw output is not accessible:**
- Add a `raw_output` field to `TurnEvent` for fumble events. Populate it from `AdapterResult.raw_response` in `game.py` during fumble handling.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** _(executor name/model)_
**Date:** _(date)_

**What was done:**

**What passed:**

**What failed or was unexpected:**

**Visual quality assessment:**

**Replay file sample size:**

**What changed from plan:**

**State left for Phase 6:**

---

## §9 Next Phase Pointer

**Next:** Phase 6 — Integration, Balance & Verification (`docs/dev/0.1.0/phase-6-integration-balance.md`)

**What Phase 6 needs from this phase:**
- Rich CLI working end-to-end.
- Match replays saved as JSON.
- All display and spectator features functional.
- Green test suite.

**What Phase 6 does NOT need from this phase:**
- Perfect visual polish (Phase 6 is about measurement, not aesthetics).
- Web GUI or streaming server.

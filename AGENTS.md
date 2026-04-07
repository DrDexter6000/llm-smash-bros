# AGENTS.md

## Start Here

- Read in this order for any non-trivial work: `README.md` → `AGENTS.md` (this file) → `docs/dev/STRATEGY.md` → `docs/dev/PRD.md` → `docs/dev/PLAN.md` → your target phase plan in `docs/dev/0.1.0/`.
- Development-doc authority is: `STRATEGY.md` > `PRD.md` > `PLAN.md` > phase TDD plans. If they conflict, higher wins.
- All development-process docs live under `docs/dev/`.
- Phase-level TDD execution plans live under `docs/dev/0.1.0/`.

## Repo Shape

- This repo is currently **backend-only in practice**. The README mentions frontend/GUI plans, but the implemented code is the Python CLI engine under `backend/`.
- Python package: `backend/src/llm_smash/`
- Main boundaries:
  - `engine/` = state, combat, validation, game loop
  - `llm/` = mock/live adapters
  - `fighters/` = roster, fighter IDs, prompts/personality (being refactored to archetype system in Phase 2)
  - `cli.py` + `__main__.py` = current runnable interface

## Commands Agents Should Actually Use

- Work from `backend/` for Python commands.
- Prefer the local venv when present: `backend/.venv/Scripts/python.exe`
- Reliable test command in this repo:
  - `backend\.venv\Scripts\python.exe -m pytest -q`
- CLI entrypoint:
  - `backend\.venv\Scripts\python.exe -m llm_smash`
- If the venv is unavailable, fall back to `uv` from `backend/`:
  - `uv run pytest -q`
  - `uv run python -m llm_smash`

## Runtime Modes

- Default run is **mock mode**. No API keys needed.
- Live mode is explicit: `python -m llm_smash --live`
- `--no-preflight` skips API connectivity checks before live matches.
- Timeout defaults are mode-specific in code:
  - mock = 8s
  - live = 30s

## Env / Provider Gotchas

- Live config is loaded from `backend/.env`, not repo root.
- Template is `backend/.env.example`.
- Each fighter slot is configured independently via `FIGHTER1_*` and `FIGHTER2_*`.
- Supported provider values are `openai` and `anthropic`.
- OpenRouter uses the `openai` protocol path, so use:
  - `PROVIDER=openai`
  - `BASE_URL=https://openrouter.ai/api/v1`
- Do not invent a separate `openrouter` provider name.

## Fighter System (v0.1.0 Transition)

**Current state:** Fighter IDs are hardcoded LLM names in `backend/src/llm_smash/fighters/roster.py` (`gpt-4o`, `claude-3.5-sonnet`, `gemini-1.5-pro`, `llama-3`). This is being replaced.

**Target state (Phase 2):** Generic archetype IDs (`striker`, `guardian`, `controller`, `berserker`). Any LLM can pilot any archetype. Match config maps model → archetype.

If you are executing Phase 1, the current fighter IDs still apply. If you are executing Phase 2+, follow the archetype system defined in `PRD §5`.

## Validation / Output Quirks

- The validator strips markdown code fences and `<think>...</think>` blocks before JSON parsing.
- Mock mode uses scripted/randomized output; live mode uses real model output.
- Fumble fallback is hardcoded defensive behavior when timeout/invalid output occurs, plus an HP penalty.

## Testing / Verification Notes

- Pytest is configured in `backend/pyproject.toml` with `asyncio_mode = auto`.
- Tests live under `backend/tests/`.
- For focused work, run the smallest relevant test file first, then full suite.
- LSP import resolution may look noisy from repo root because the Python package lives under `backend/src`; trust the test run from `backend/` more than root-level import diagnostics.
- **Run the full test suite after every significant change.** Do not batch multiple features before testing.

## Known Repo-Specific Traps

- `backend/src/llm_smash/__main__.py` contains duplicated argument-parsing/run logic. **Phase 1 fixes this.** Do not assume the file is clean.
- Some ability descriptions in `roster.py` reference unimplemented effects (stun, slow, reflection, absorb). **Phase 1 removes these lies.** If you are executing Phase 2+, this should already be fixed.
- There is no verified root `.gitignore`; ignore rules relevant to Python work are in `backend/.gitignore`.
- `backend/.env` may contain real API keys. **Never commit this file.** Phase 1 adds root `.gitignore` coverage.
- `backend/uv.lock` is gitignored; do not assume lockfile-based reproducibility is committed.

## When Updating Docs

- If a change affects product meaning, update `docs/dev/` in the same change.
- Use `document + section number` references (`PRD §5.2`, `PLAN §4 Phase 2`) rather than relying on line numbers.

## TDD Plan Discipline

- If you create or revise a TDD plan, scale the structure to the actual task size. Decide deliberately whether the work needs separate tasks; do not split mechanically, and do not collapse complex work into one blob.
- Each phase plan must be a self-contained execution loop with: goal, execution rules, tasks, acceptance criteria, self-audit, self-optimization, writeback, and next-phase pointer.
- The execution writeback is mandatory. After completing a phase, append a short execution brief to the end of that phase plan covering what was done, what passed, what failed, what changed from plan, and what the next phase is starting with.
- Plans should preserve forward motion. Once a phase is complete and its writeback is recorded, the next phase should be obvious enough to start without re-deriving the whole plan.
- Do not expand scope beyond your assigned phase. If you discover the plan is wrong, document it in the writeback — do not silently fix it by doing extra work.

## Prompt Budget Rule

Per `STRATEGY §4` and `PRD §7.3`, the total prompt sent to LLMs (system prompt + battle state + recent history + rules reminder) must stay under **2000 tokens**. Measure this when changing prompts. Prefer ASCII grid over verbose JSON for spatial data.

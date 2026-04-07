# AGENTS.md

## Start Here

- Read in this order for any non-trivial work: `README.md` → `docs/dev/STRATEGY.md` → `docs/dev/PRD.md` → `docs/dev/PLAN.md` → `docs/dev/README.md`.
- Development-doc authority is: `STRATEGY.md` > `PRD.md` > `PLAN.md`. If they conflict, higher wins.
- All development-process docs live under `docs/dev/`.

## Repo Shape

- This repo is currently **backend-only in practice**. The README mentions frontend/FastAPI/WebSocket plans, but the implemented code is the Python CLI engine under `backend/`.
- Python package: `backend/src/llm_smash/`
- Main boundaries:
  - `engine/` = state, combat, validation, game loop
  - `llm/` = mock/live adapters
  - `fighters/` = roster, fighter IDs, prompts/personality
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
- Each fighter is configured independently via `FIGHTER1_*` and `FIGHTER2_*`.
- Supported provider values are `openai` and `anthropic`.
- OpenRouter uses the `openai` protocol path, so use:
  - `PROVIDER=openai`
  - `BASE_URL=https://openrouter.ai/api/v1`
- Do not invent a separate `openrouter` provider name.

## Fighter IDs

Valid fighter IDs are fixed in `backend/src/llm_smash/fighters/roster.py`:

- `gpt-4o`
- `claude-3.5-sonnet`
- `gemini-1.5-pro`
- `llama-3`

## Validation / Output Quirks

- The validator strips markdown code fences and `<think>...</think>` blocks before JSON parsing.
- Mock mode uses scripted/randomized output; live mode uses real model output.
- Fumble fallback is hardcoded defensive behavior when timeout/invalid output occurs.

## Testing / Verification Notes

- Pytest is configured in `backend/pyproject.toml` with `asyncio_mode = auto`.
- Tests live under `backend/tests/`.
- For focused work, run the smallest relevant test file first, then full suite.
- LSP import resolution may look noisy from repo root because the Python package lives under `backend/src`; trust the test run from `backend/` more than root-level import diagnostics.

## Known Repo-Specific Traps

- `backend/src/llm_smash/__main__.py` currently contains duplicated argument-parsing/run logic. Don’t assume the file is clean just because the CLI works.
- There is no verified root `.gitignore`; ignore rules relevant to Python work are in `backend/.gitignore`.
- `backend/uv.lock` is gitignored here, so do not assume lockfile-based reproducibility is committed.

## When Updating Docs

- If a change affects product meaning, update `docs/dev/` in the same change.
- Use `document + section number` references (`PRD §5.2`, `PLAN §5 Phase C`) rather than relying on line numbers.

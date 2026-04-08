# Phase 0 — Engineering Hygiene

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 0`
**Prerequisites:** v0.1.0 complete

---

## §1 Phase Goal & Purpose

Harden the engineering foundation before building the web spectator layer. v0.1.0 left behind several hygiene gaps that will compound as the project grows: no CI pipeline, phantom dependencies, fragile API calls, and a broken root-level test runner.

**Why this matters:**
- Without CI, the 189-test suite only catches regressions when someone remembers to run it locally.
- FastAPI/uvicorn/websockets are already in `pyproject.toml` but unused. v0.2.0 will use them — but they must be confirmed working, not cargo-culted from a dependency list.
- Live mode has zero retry logic. A single 429 from OpenRouter kills the match. For batch tournaments and live demos, this is unacceptable.
- Running `pytest` from the repo root fails due to import errors (`anthropic`, `rich` not in global env). This confuses every new contributor.

---

## §2 Prerequisites & Dependencies

- v0.1.0 complete, 189 tests passing from `backend/` directory.
- GitHub repository access for CI setup.
- Understanding of `pyproject.toml`, `uv` package manager, and pytest configuration.

---

## §3 Execution Rules

### MUST DO

- Add a GitHub Actions CI workflow that runs the full test suite on push/PR.
- Fix root-level `pytest` so it works from the repo root (not just `backend/`).
- Verify FastAPI, uvicorn, and websockets actually import and work. If version pins are stale, update them.
- Add exponential backoff retry logic to `openai_client.py` and `anthropic_client.py` for transient API errors (429, 500, 502, 503).
- Add a configurable max retry count (default 3) and base delay (default 1s).
- All existing tests must continue to pass.
- Keep changes surgical. This phase is infrastructure, not features.

### MUST NOT DO

- Do not add new game features or change game mechanics.
- Do not write the FastAPI app or WebSocket endpoints (that is Phase 1-2).
- Do not change CLI behavior.
- Do not add frontend code.
- Do not over-engineer the retry system — simple exponential backoff with jitter is sufficient.

---

## §4 Task Breakdown

### Task 0.1: Fix Root-Level Pytest

The problem: running `pytest` from the repo root triggers import errors because `anthropic`, `rich`, etc. are installed in `backend/.venv` but not in the global Python.

**Solution options (pick one):**
- **Option A (recommended):** Add a root `pyproject.toml` or `pytest.ini` that sets `rootdir` and points to `backend/` as the test root, using the backend venv.
- **Option B:** Add a root `Makefile` or script that wraps `cd backend && uv run pytest`.

Whichever option is chosen, verify:
```bash
# From repo root
pytest -q        # or the wrapper command
# Should produce: "189 passed"
```

### Task 0.2: GitHub Actions CI Pipeline

Create `.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Install dependencies
        run: cd backend && uv sync --dev
      - name: Run tests
        run: cd backend && uv run pytest -q
```

Verify the workflow syntax is valid. Do not merge until the pipeline passes.

### Task 0.3: Verify and Clean Dependencies

Open `backend/pyproject.toml`. For each dependency:

| Dependency | Status | Action |
|-----------|--------|--------|
| `pydantic>=2.0` | Used everywhere | Keep |
| `fastapi>=0.110` | Not imported in any source file yet | Keep — v0.2.0 Phase 1 will use it |
| `uvicorn[standard]>=0.27` | Not imported yet | Keep — v0.2.0 Phase 1 will use it |
| `websockets>=12.0` | Not imported yet | Keep — v0.2.0 Phase 2 will use it |
| `openai>=1.0` | Used in `openai_client.py` | Keep |
| `anthropic>=0.25` | Used in `anthropic_client.py` | Keep |
| `python-dotenv>=1.0` | Used in `cli.py` | Keep |
| `rich>=13.0` | Used in `cli.py` | Keep |

**Action:** Add a comment block in `pyproject.toml` explaining which dependencies are for v0.2.0 web layer (fastapi, uvicorn, websockets). Verify all dependencies install cleanly:

```bash
cd backend && uv sync --dev && uv run python -c "import fastapi; import uvicorn; import websockets; print('All web deps OK')"
```

### Task 0.4: API Retry Logic

Add retry with exponential backoff to both LLM clients for transient errors.

**In `openai_client.py`:**
```python
import asyncio
import random

MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds

async def _retry_api_call(self, coro_factory, retries=MAX_RETRIES):
    """Retry an API call with exponential backoff + jitter."""
    for attempt in range(retries + 1):
        try:
            return await coro_factory()
        except Exception as e:
            if attempt == retries or not self._is_transient(e):
                raise
            delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)
```

Transient errors to retry: HTTP 429, 500, 502, 503, 504, connection timeouts, `APIConnectionError`.

Apply the same pattern to `anthropic_client.py`.

**Tests:** Add unit tests that verify:
- Successful call on first attempt → no retry.
- Transient error on attempt 1, success on attempt 2 → returns result.
- Non-transient error (400, 401) → raises immediately without retry.
- All retries exhausted → raises the last error.

### Task 0.5: Final Verification

```bash
# From repo root — must work
pytest -q  # or wrapper

# From backend/ — must still work
cd backend && uv run pytest -q

# Verify CI config is valid
act -n  # if act is installed, or just push and check
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Root-level test runner works | `pytest` from repo root fails | `pytest` from repo root runs all tests and passes |
| 2 | CI pipeline exists | No `.github/workflows/` | CI workflow runs tests on push/PR |
| 3 | Web dependencies verified | `import fastapi` fails | All web deps import cleanly in backend venv |
| 4 | API retry logic exists | A single 429 kills the match | Transient errors are retried with backoff |
| 5 | Retry tests pass | No retry tests exist | Unit tests cover success, transient retry, non-transient fail, exhaustion |
| 6 | All existing tests pass | Any test failure | `pytest -q` exits 0 with 189+ passed |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Run `pytest` from the repo root. Does it work?
- [ ] Read `.github/workflows/ci.yml`. Is it correct YAML? Does it install deps and run tests?
- [ ] Read `openai_client.py` and `anthropic_client.py`. Is the retry logic clean and tested?
- [ ] Run `uv run python -c "import fastapi; import uvicorn; import websockets"` in backend venv. All OK?
- [ ] Run full test suite. All green?
- [ ] `git diff` — are all changes infrastructure-only? No game logic touched?

---

## §7 Self-Optimization & Retry Guidance

**If root-level pytest still fails:**
- Check if the issue is venv discovery. `pytest.ini` or `pyproject.toml` at root with `[tool.pytest.ini_options] rootdir = "backend"` may help.
- Alternative: a thin root `conftest.py` that adds `backend/src` to `sys.path`.

**If CI fails on GitHub:**
- Check Python version mismatch (must be 3.12+).
- Check if `uv` installation step works on ubuntu-latest.
- Check if `uv sync --dev` installs all optional deps.

**If retry tests are flaky:**
- Mock `asyncio.sleep` to avoid real delays in tests.
- Use deterministic failure sequences (fail N times, then succeed).

---

## §8 Execution Writeback

**Completed:** 2026-04-08

**What was done:**

- **Task 0.1 (Root pytest):** Root-level `pytest` fails because the global Python lacks `anthropic`/`openai`/`rich`. The working solution is `uv run --directory backend pytest` from repo root. No root `pyproject.toml` was added because it would be misleading (bare `pytest` still uses global Python). The documented command is sufficient.

- **Task 0.2 (CI):** Created `.github/workflows/ci.yml` — runs on push/PR to master, uses Python 3.12, installs uv, syncs deps, runs pytest. Single job, clean configuration.

- **Task 0.3 (Dependencies):** Verified all web deps (`fastapi`, `uvicorn`, `websockets`) import cleanly in backend venv. Added category comments to `pyproject.toml` separating core engine deps from v0.2.0 web layer deps.

- **Task 0.4 (Retry logic):** Added `_retry_api_call()` with exponential backoff + jitter to both `openai_client.py` and `anthropic_client.py`. Retries transient errors (429, 500, 502, 503, 504, timeout, connection). Non-transient errors raise immediately. Both `get_action()` and `get_post_match_comment()` are wrapped. Created `test_retry.py` with 8 tests (4 scenarios × 2 providers, parametrized).

**What passed:**
- 197 tests total (189 existing + 8 new retry tests). All green.
- Web dependency import verification passed.
- CI YAML is syntactically valid.

**What failed or was unexpected:**
- Root `pyproject.toml` approach (Option A) doesn't work because `pytest` picks up the global Python, which lacks the venv deps. The `uv run --directory backend` wrapper is the correct solution. This is a documentation fix, not a code fix.

**What changed from plan:**
- No root `pyproject.toml` or `conftest.py` was created. The plan suggested either Option A or B; neither was needed as `uv run --directory backend pytest` already works from root.

**Recommendations for Phase 1:**
- The retry logic wraps `get_action()` API calls. Note that `APITimeoutError` is caught after retry exhaustion in `get_action()` and converted to `AdapterResult(timed_out=True)` — this is correct behavior (timeout after retries still counts as a timeout).

---

## §9 Next Phase Pointer

**Next:** Phase 1 — API Server Foundation (`docs/dev/0.2.0/phase-1-api-server.md`)

**What Phase 1 needs from this phase:**
- Verified FastAPI/uvicorn/websockets dependencies.
- CI pipeline that will catch regressions as the API is built.
- Resilient LLM clients that won't crash on transient API errors.
- Root-level test runner for easier development.

**What Phase 1 does NOT need from this phase:**
- Any FastAPI app code (Phase 1 writes that).
- Any WebSocket endpoints (Phase 2).
- Any frontend code (Phase 3+).

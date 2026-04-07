# LLM Smash Bros — MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working concept verification where two LLMs (GPT-4o and Claude) fight a complete turn-based match, with output visible in CLI and a basic web frontend.

**Architecture:** Python async game engine with Pydantic state models, FastAPI WebSocket server, unified LLM adapter layer with mock/real backends, and a React TypeScript frontend for visualization.

**Tech Stack:** Python 3.12+, Pydantic v2, FastAPI, pytest, React 18, TypeScript, Vitest, uv (Python), pnpm (Node)

---

## Phase 1: Foundation — State Models & Combat Math

*No external dependencies. Pure data models and deterministic logic. This is the core that everything else builds on.*

### Task 1.1: Project Scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/llm_smash/__init__.py`
- Create: `backend/src/llm_smash/engine/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Initialize Python project with uv**

```bash
cd backend
uv init --name llm-smash --lib
```

Manually adjust `pyproject.toml` to include:
```toml
[project]
name = "llm-smash"
version = "0.1.0"
description = "LLM Smash Bros - Turn-based AI fighting game"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "websockets>=12.0",
    "openai>=1.0",
    "anthropic>=0.25",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Install dependencies**

```bash
uv sync --all-extras
```

- [ ] **Step 3: Verify pytest runs (empty test suite)**

```bash
uv run pytest -v
```
Expected: 0 tests collected, exit 0.

- [ ] **Step 4: Commit**

---

### Task 1.2: Core State Models (Pydantic)

**Files:**
- Create: `backend/src/llm_smash/engine/state.py`
- Create: `backend/tests/test_state.py`

- [ ] **Step 1: Write failing tests for state models**

```python
# backend/tests/test_state.py
import pytest
from llm_smash.engine.state import (
    Position, Ability, StatusEffect, Fighter, Hazard, Arena, BattleState,
    ActionResponse, ActionType, MoveDirection, MatchPhase
)

class TestPosition:
    def test_create_position(self):
        pos = Position(x=3, y=2)
        assert pos.x == 3 and pos.y == 2

    def test_distance_to(self):
        a = Position(x=0, y=0)
        b = Position(x=3, y=4)
        assert a.distance_to(b) == 5.0  # Euclidean

    def test_chebyshev_distance(self):
        a = Position(x=0, y=0)
        b = Position(x=3, y=4)
        assert a.chebyshev_distance(b) == 4  # Max of dx, dy (for grid movement)

class TestFighter:
    def test_create_fighter(self):
        fighter = Fighter(
            id="gpt-4o",
            codename="The Oracle",
            hp=100, max_hp=100,
            energy=100, max_energy=100,
            position=Position(x=0, y=0),
            abilities=[],
            status_effects=[],
        )
        assert fighter.hp == 100
        assert fighter.is_alive

    def test_fighter_dead_at_zero_hp(self):
        fighter = Fighter(
            id="gpt-4o", codename="The Oracle",
            hp=0, max_hp=100, energy=100, max_energy=100,
            position=Position(x=0, y=0), abilities=[], status_effects=[],
        )
        assert not fighter.is_alive

    def test_fighter_hp_clamped(self):
        fighter = Fighter(
            id="gpt-4o", codename="The Oracle",
            hp=150, max_hp=100, energy=100, max_energy=100,
            position=Position(x=0, y=0), abilities=[], status_effects=[],
        )
        assert fighter.hp == 100  # Clamped to max

class TestBattleState:
    def test_create_battle_state(self):
        f1 = Fighter(
            id="gpt-4o", codename="The Oracle",
            hp=100, max_hp=100, energy=100, max_energy=100,
            position=Position(x=0, y=0), abilities=[], status_effects=[],
        )
        f2 = Fighter(
            id="claude-3.5-sonnet", codename="The Artisan",
            hp=85, max_hp=85, energy=100, max_energy=100,
            position=Position(x=7, y=5), abilities=[], status_effects=[],
        )
        arena = Arena(width=8, height=6, hazards=[])
        state = BattleState(
            match_id="test-001", turn=1, phase=MatchPhase.FIGHTING,
            fighters=[f1, f2], arena=arena,
        )
        assert state.turn == 1
        assert len(state.fighters) == 2

class TestActionResponse:
    def test_valid_action_response(self):
        resp = ActionResponse(
            turn=5,
            action={"type": "attack", "ability": "Code Slice", "target": "gpt-4o"},
            move={"direction": "left"},
            inner_monologue="Going in for the kill.",
            trash_talk="GG no re.",
        )
        assert resp.turn == 5
        assert resp.action["type"] == "attack"

    def test_defend_action(self):
        resp = ActionResponse(
            turn=5,
            action={"type": "defend"},
            move=None,
            inner_monologue="Playing it safe.",
            trash_talk="Come at me.",
        )
        assert resp.action["type"] == "defend"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest backend/tests/test_state.py -v
```
Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Implement state models**

Create `backend/src/llm_smash/engine/state.py` with all Pydantic models:
- `Position` (with `distance_to` and `chebyshev_distance` methods)
- `Ability` (name, type, damage, energy_cost, cooldown, cooldown_remaining, range, description)
- `StatusEffect` (name, turns_remaining, effect_type, value)
- `Fighter` (all fields per PRD Section 3.2, with `is_alive` property and HP/energy clamping via validators)
- `Hazard` (type, position, damage/effect, turns_remaining)
- `Arena` (width, height, hazards list)
- `BattleState` (match_id, turn, phase, fighters, arena)
- `ActionResponse` (turn, action, move, inner_monologue, trash_talk)
- `MatchPhase` enum: INIT, READY, FIGHTING, RESOLVED
- `ActionType` enum: ATTACK, DEFEND, WAIT
- `MoveDirection` enum: UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest backend/tests/test_state.py -v
```
Expected: All tests pass.

- [ ] **Step 5: Commit** — "feat: core state models (Position, Fighter, Arena, BattleState, ActionResponse)"

---

### Task 1.3: Combat Resolution Engine

**Files:**
- Create: `backend/src/llm_smash/engine/combat.py`
- Create: `backend/tests/test_combat.py`

- [ ] **Step 1: Write failing tests for combat resolution**

```python
# backend/tests/test_combat.py
import pytest
from unittest.mock import patch
from llm_smash.engine.combat import CombatResolver
from llm_smash.engine.state import Position, Fighter, Ability, ActionResponse

@pytest.fixture
def basic_ability():
    return Ability(
        name="Logic Missile", type="attack", damage=12,
        energy_cost=0, cooldown=0, cooldown_remaining=0, range=4,
    )

@pytest.fixture
def attacker(basic_ability):
    return Fighter(
        id="gpt-4o", codename="The Oracle",
        hp=100, max_hp=100, energy=100, max_energy=100,
        position=Position(x=0, y=0),
        abilities=[basic_ability], status_effects=[],
    )

@pytest.fixture
def defender():
    return Fighter(
        id="claude", codename="The Artisan",
        hp=85, max_hp=85, energy=100, max_energy=100,
        position=Position(x=2, y=0),
        abilities=[], status_effects=[],
    )

class TestCombatResolver:
    def test_calculate_damage_basic(self, attacker, defender, basic_ability):
        resolver = CombatResolver(seed=42)  # Deterministic for testing
        dmg = resolver.calculate_damage(attacker, defender, basic_ability, is_defending=False)
        assert 10 <= dmg <= 19  # 12 base ± 15% variance, potential crit

    def test_distance_penalty_applied(self, attacker, defender, basic_ability):
        defender.position = Position(x=6, y=0)  # Distance 6, range 4 → penalty
        resolver = CombatResolver(seed=42)
        dmg = resolver.calculate_damage(attacker, defender, basic_ability, is_defending=False)
        assert dmg < 12  # Should be reduced by distance penalty

    def test_defend_reduces_damage(self, attacker, defender, basic_ability):
        resolver = CombatResolver(seed=42)
        normal = resolver.calculate_damage(attacker, defender, basic_ability, is_defending=False)
        defended = resolver.calculate_damage(attacker, defender, basic_ability, is_defending=True)
        assert defended < normal  # 20% reduction

    def test_resolve_movement_valid(self, attacker):
        resolver = CombatResolver(seed=42)
        new_pos = resolver.resolve_movement(attacker, "right", arena_width=8, arena_height=6)
        assert new_pos == Position(x=1, y=0)

    def test_resolve_movement_blocked_by_boundary(self, attacker):
        attacker.position = Position(x=0, y=0)
        resolver = CombatResolver(seed=42)
        new_pos = resolver.resolve_movement(attacker, "left", arena_width=8, arena_height=6)
        assert new_pos == Position(x=0, y=0)  # Clamped to grid

    def test_energy_regen_per_turn(self, attacker):
        attacker.energy = 50
        resolver = CombatResolver(seed=42)
        resolver.apply_energy_regen(attacker)
        assert attacker.energy == 55  # +5 per turn

    def test_energy_capped_at_max(self, attacker):
        attacker.energy = 98
        resolver = CombatResolver(seed=42)
        resolver.apply_energy_regen(attacker)
        assert attacker.energy == 100  # Capped
```

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement CombatResolver**

Key methods:
- `calculate_damage(attacker, defender, ability, is_defending)` → int
- `resolve_movement(fighter, direction, arena_width, arena_height)` → Position
- `apply_energy_regen(fighter)` → None
- `apply_ability_cooldowns(fighter)` → None (tick down cooldowns by 1)
- `apply_hazard_damage(fighter, hazards)` → int (total hazard damage taken)

Use seeded `random.Random` instance for deterministic testing.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: combat resolution engine (damage, movement, energy)"

---

### Task 1.4: Fighter Roster Definitions

**Files:**
- Create: `backend/src/llm_smash/fighters/__init__.py`
- Create: `backend/src/llm_smash/fighters/roster.py`
- Create: `backend/tests/test_roster.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_roster.py
from llm_smash.fighters.roster import get_fighter, get_all_fighters, FIGHTER_IDS

class TestRoster:
    def test_get_all_fighters_returns_four(self):
        fighters = get_all_fighters()
        assert len(fighters) == 4

    def test_each_fighter_has_required_fields(self):
        for fighter in get_all_fighters():
            assert fighter.id in FIGHTER_IDS
            assert fighter.max_hp > 0
            assert fighter.max_energy > 0
            assert len(fighter.abilities) >= 2  # Basic + ability + ultimate

    def test_get_fighter_by_id(self):
        oracle = get_fighter("gpt-4o")
        assert oracle.codename == "The Oracle"
        assert oracle.hp == 100

    def test_get_fighter_unknown_raises(self):
        import pytest
        with pytest.raises(ValueError):
            get_fighter("unknown-model")
```

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement roster.py**

Define all 4 fighters per PRD Section 4, with their abilities, stats, and system prompt personalities.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: fighter roster with 4 fighters (Oracle, Artisan, Observer, Swarm)"

---

## Phase 2: Response Validation & Mock LLM Adapter

*Still no external API calls. Build the validation layer and a mock adapter so the game can run end-to-end without spending money.*

### Task 2.1: Response Validator

**Files:**
- Create: `backend/src/llm_smash/engine/validator.py`
- Create: `backend/tests/test_validator.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_validator.py
import pytest
from llm_smash.engine.validator import ResponseValidator
from llm_smash.engine.state import BattleState, Fighter, Arena, Position, Ability, MatchPhase

@pytest.fixture
def sample_state():
    """A minimal valid battle state for validation context."""
    # ... (build a BattleState with 2 fighters, abilities, grid)
    pass

class TestResponseValidator:
    def test_valid_json_passes(self, sample_state):
        validator = ResponseValidator()
        raw = '{"turn": 1, "action": {"type": "attack", "ability": "Logic Missile", "target": "claude-3.5-sonnet"}, "move": {"direction": "right"}, "inner_monologue": "test", "trash_talk": "test"}'
        result = validator.validate(raw, turn=1, fighter_id="gpt-4o", state=sample_state)
        assert result.is_valid
        assert result.response.turn == 1

    def test_invalid_json_rejected(self, sample_state):
        validator = ResponseValidator()
        result = validator.validate("not json at all", turn=1, fighter_id="gpt-4o", state=sample_state)
        assert not result.is_valid
        assert "json" in result.error.lower()

    def test_stale_turn_rejected(self, sample_state):
        validator = ResponseValidator()
        raw = '{"turn": 99, "action": {"type": "defend"}, "move": null, "inner_monologue": "x", "trash_talk": "x"}'
        result = validator.validate(raw, turn=1, fighter_id="gpt-4o", state=sample_state)
        assert not result.is_valid
        assert "turn" in result.error.lower()

    def test_ability_on_cooldown_rejected(self, sample_state):
        # Set ability cooldown > 0, then try to use it
        validator = ResponseValidator()
        # ... build raw JSON referencing ability on cooldown
        # assert not result.is_valid

    def test_out_of_energy_rejected(self, sample_state):
        # Fighter has 10 energy, ability costs 80
        validator = ResponseValidator()
        # ... assert not result.is_valid

    def test_movement_off_grid_clamped(self, sample_state):
        # Fighter at edge, tries to move off
        validator = ResponseValidator()
        # ... result should be valid but movement clamped/nullified
```

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement ResponseValidator**

Methods:
- `validate(raw_json: str, turn: int, fighter_id: str, state: BattleState) -> ValidationResult`
- `ValidationResult` dataclass: `is_valid: bool`, `response: ActionResponse | None`, `error: str | None`

Checks: JSON parse → Pydantic parse → turn echo → ability exists → ability not on cooldown → enough energy → move legality.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: response validator with JSON, schema, turn echo, and game rule checks"

---

### Task 2.2: LLM Adapter Interface + Mock Adapter

**Files:**
- Create: `backend/src/llm_smash/llm/__init__.py`
- Create: `backend/src/llm_smash/llm/adapter.py`
- Create: `backend/src/llm_smash/llm/mock_client.py`
- Create: `backend/tests/test_adapter.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_adapter.py
import pytest
import asyncio
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.mock_client import MockLLMClient
from llm_smash.engine.state import BattleState  # ... minimal state fixture

class TestMockLLMClient:
    @pytest.mark.asyncio
    async def test_mock_returns_valid_json(self):
        client = MockLLMClient(fighter_id="gpt-4o")
        state = ...  # minimal BattleState
        response = await client.get_action(state, turn=1)
        assert '"turn"' in response  # Raw JSON string
        assert '"action"' in response

    @pytest.mark.asyncio
    async def test_mock_respects_timeout(self):
        client = MockLLMClient(fighter_id="gpt-4o", latency_ms=100)
        state = ...
        response = await asyncio.wait_for(client.get_action(state, turn=1), timeout=1.0)
        assert response is not None

class TestLLMAdapter:
    @pytest.mark.asyncio
    async def test_adapter_with_mock_backend(self):
        adapter = LLMAdapter(backend=MockLLMClient(fighter_id="gpt-4o"))
        state = ...
        result = await adapter.request_action(state, turn=1, timeout=5.0)
        assert result.raw_response is not None

    @pytest.mark.asyncio
    async def test_adapter_timeout_returns_none(self):
        client = MockLLMClient(fighter_id="gpt-4o", latency_ms=10000)  # 10s
        adapter = LLMAdapter(backend=client)
        state = ...
        result = await adapter.request_action(state, turn=1, timeout=0.1)  # 100ms
        assert result.timed_out
```

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement adapter and mock client**

`LLMAdapter` (abstract interface):
- `async request_action(state, turn, timeout) -> AdapterResult`
- `AdapterResult`: `raw_response: str | None`, `timed_out: bool`, `latency_ms: float`

`MockLLMClient`:
- Generates random but VALID action responses based on fighter's available abilities
- Configurable: `latency_ms`, `failure_rate` (% of invalid JSON for testing), `personality` (trash talk style)

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: LLM adapter interface + mock client for dev/testing"

---

## Phase 3: Game Loop — Tying It All Together

*The game can now run a complete match with mock LLMs. This is the concept verification milestone.*

### Task 3.1: Turn Manager & Game Loop

**Files:**
- Create: `backend/src/llm_smash/engine/game.py`
- Create: `backend/tests/test_game.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_game.py
import pytest
from llm_smash.engine.game import GameEngine, MatchConfig, MatchResult
from llm_smash.llm.mock_client import MockLLMClient

class TestGameEngine:
    @pytest.mark.asyncio
    async def test_match_runs_to_completion(self):
        config = MatchConfig(
            fighter_ids=["gpt-4o", "claude-3.5-sonnet"],
            max_turns=50,
            timeout_per_turn=5.0,
        )
        engine = GameEngine(
            config=config,
            llm_clients={
                "gpt-4o": MockLLMClient(fighter_id="gpt-4o"),
                "claude-3.5-sonnet": MockLLMClient(fighter_id="claude-3.5-sonnet"),
            }
        )
        result = await engine.run_match()
        assert result.winner is not None or result.is_draw
        assert result.total_turns > 0
        assert result.total_turns <= 50

    @pytest.mark.asyncio
    async def test_match_ends_on_ko(self):
        # Use mock that always attacks → eventually someone dies
        config = MatchConfig(
            fighter_ids=["gpt-4o", "claude-3.5-sonnet"],
            max_turns=100,  # High limit, should KO before this
            timeout_per_turn=5.0,
        )
        engine = GameEngine(
            config=config,
            llm_clients={
                "gpt-4o": MockLLMClient(fighter_id="gpt-4o"),
                "claude-3.5-sonnet": MockLLMClient(fighter_id="claude-3.5-sonnet"),
            }
        )
        result = await engine.run_match()
        assert result.winner is not None

    @pytest.mark.asyncio
    async def test_fumble_on_timeout(self):
        # Mock with 100% timeout
        config = MatchConfig(
            fighter_ids=["gpt-4o", "claude-3.5-sonnet"],
            max_turns=5,
            timeout_per_turn=0.01,  # 10ms, mock will exceed
        )
        engine = GameEngine(
            config=config,
            llm_clients={
                "gpt-4o": MockLLMClient(fighter_id="gpt-4o", latency_ms=5000),
                "claude-3.5-sonnet": MockLLMClient(fighter_id="claude-3.5-sonnet", latency_ms=5000),
            }
        )
        result = await engine.run_match()
        assert result.total_fumbles > 0

    @pytest.mark.asyncio
    async def test_turn_log_recorded(self):
        config = MatchConfig(
            fighter_ids=["gpt-4o", "claude-3.5-sonnet"],
            max_turns=3,
            timeout_per_turn=5.0,
        )
        engine = GameEngine(
            config=config,
            llm_clients={
                "gpt-4o": MockLLMClient(fighter_id="gpt-4o"),
                "claude-3.5-sonnet": MockLLMClient(fighter_id="claude-3.5-sonnet"),
            }
        )
        result = await engine.run_match()
        assert len(result.turn_log) == result.total_turns
        assert all(log.turn_number > 0 for log in result.turn_log)
```

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement GameEngine**

Core class `GameEngine`:
- `__init__(config, llm_clients, event_callback=None)`
- `async run_match() -> MatchResult`
- Internal: `async _execute_turn(turn_num) -> TurnLog`
- Internal: `_check_end_conditions() -> MatchResult | None`
- Internal: `_spawn_hazard(turn_num)` (every 5 turns, doubled after turn 40)

`MatchConfig`: fighter_ids, max_turns, timeout_per_turn, seed
`MatchResult`: winner, is_draw, total_turns, total_fumbles, turn_log, final_state
`TurnLog`: turn_number, actions (per fighter), state_snapshot, events

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: game engine with complete match lifecycle"

---

### Task 3.2: CLI Runner (Concept Verification!)

**Files:**
- Create: `backend/src/llm_smash/cli.py`
- Create: `backend/tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_cli.py
import pytest
from unittest.mock import patch
from llm_smash.cli import run_cli_match

class TestCLI:
    @pytest.mark.asyncio
    async def test_cli_match_completes(self, capsys):
        result = await run_cli_match(
            fighter_ids=["gpt-4o", "claude-3.5-sonnet"],
            use_mock=True,
            max_turns=10,
        )
        captured = capsys.readouterr()
        assert "Turn 1" in captured.out
        assert "Winner" in captured.out or "Draw" in captured.out
```

- [ ] **Step 2: Run test — verify it fails**

- [ ] **Step 3: Implement CLI runner**

A simple async function that:
1. Creates GameEngine with mock or real LLM clients
2. Runs the match
3. Prints each turn with colored output:
   - Turn number + fighter HP bars
   - Each fighter's action + inner monologue
   - Trash talk in quotes
   - Damage dealt, status effects applied
   - ASCII art for special events (KO, critical hit, fumble)
4. Prints match summary at end

Add `__main__.py` or CLI entry point:
```bash
uv run python -m llm_smash --mock  # Mock mode
uv run python -m llm_smash --fighters gpt-4o claude-3.5-sonnet  # Real APIs
```

- [ ] **Step 4: Run test — verify it passes**

- [ ] **Step 5: Run a full mock match manually and verify it's entertaining**

```bash
uv run python -m llm_smash --mock --max-turns 20
```

- [ ] **Step 6: Commit** — "feat: CLI runner for mock battles — concept verification milestone"

---

## Phase 4: Real LLM Integration

*Now connect real APIs. This is where prompt engineering matters.*

### Task 4.1: OpenAI Client

**Files:**
- Create: `backend/src/llm_smash/llm/openai_client.py`
- Create: `backend/tests/test_openai_client.py`

- [ ] **Step 1: Write failing tests (with mock httpx)**

Test that:
- Client formats system prompt + battle state correctly
- Client uses `response_format: { type: "json_object" }` for structured output
- Client handles timeout gracefully
- Client returns raw JSON string

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement OpenAI client**

Uses `openai` SDK async client. System prompt from fighter template (PRD 3.6). Uses JSON mode for reliable output.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: OpenAI LLM client with JSON mode"

---

### Task 4.2: Anthropic Client

**Files:**
- Create: `backend/src/llm_smash/llm/anthropic_client.py`
- Create: `backend/tests/test_anthropic_client.py`

- [ ] **Step 1: Write failing tests (with mock httpx)**

Same test structure as OpenAI, but:
- Anthropic doesn't have native JSON mode → heavier prompt engineering
- Test that JSON is extracted from potentially wrapped response

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement Anthropic client**

Uses `anthropic` SDK async client. Extra prompt emphasis on JSON-only output. Regex extraction of JSON from response if model wraps it in markdown.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: Anthropic LLM client with JSON extraction"

---

### Task 4.3: First Real API Match

- [ ] **Step 1: Create `.env.example` and `.gitignore`**

```
# .env.example
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

- [ ] **Step 2: Run a real match (manual integration test)**

```bash
uv run python -m llm_smash --fighters gpt-4o claude-3.5-sonnet --max-turns 10
```

- [ ] **Step 3: Debug prompt issues, iterate on system prompt template**

This WILL require iteration. Common issues:
- Models wrapping JSON in markdown code blocks
- Models adding extra fields
- Models refusing "combat" framing
- Models writing inner_monologue about being an AI, not about the game

- [ ] **Step 4: Commit** — "feat: first real API match between GPT-4o and Claude"

---

## Phase 5: WebSocket API Server

*Make the game accessible over the network for the frontend.*

### Task 5.1: FastAPI App + REST Endpoints

**Files:**
- Create: `backend/src/llm_smash/api/__init__.py`
- Create: `backend/src/llm_smash/api/routes.py`
- Create: `backend/src/llm_smash/main.py`
- Create: `backend/tests/test_routes.py`

- [ ] **Step 1: Write failing tests**

Test endpoints:
- `GET /api/health` → 200
- `GET /api/fighters` → returns roster
- `POST /api/match/start` → starts a match, returns match_id
- `GET /api/match/{match_id}/status` → returns current state

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement routes + FastAPI app**

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: FastAPI REST endpoints for match management"

---

### Task 5.2: WebSocket Endpoint

**Files:**
- Create: `backend/src/llm_smash/api/websocket.py`
- Create: `backend/tests/test_websocket.py`

- [ ] **Step 1: Write failing tests**

Test that:
- Client can connect to `/ws/match/{match_id}`
- Client receives turn updates as JSON
- Multiple clients can watch same match
- Connection handles match completion

- [ ] **Step 2: Run tests — verify they fail**

- [ ] **Step 3: Implement WebSocket manager**

GameEngine gets an `event_callback` that pushes turn results to all connected WebSocket clients.

- [ ] **Step 4: Run tests — verify they pass**

- [ ] **Step 5: Commit** — "feat: WebSocket endpoint for real-time match streaming"

---

## Phase 6: Web Frontend (Basic)

*Minimal viable UI to watch battles. Entertainment comes from the content, not the graphics.*

### Task 6.1: React Project Scaffolding

**Files:**
- Create: `frontend/` (full React project via Vite)

- [ ] **Step 1: Scaffold React + TypeScript project**

```bash
cd frontend
pnpm create vite . --template react-ts
pnpm install
```

- [ ] **Step 2: Verify it builds and runs**

```bash
pnpm dev
pnpm build
```

- [ ] **Step 3: Commit** — "feat: frontend scaffolding (React + TypeScript + Vite)"

---

### Task 6.2: TypeScript Types + WebSocket Hook

**Files:**
- Create: `frontend/src/types/game.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Define TypeScript types matching backend Pydantic models**

- [ ] **Step 2: Implement useWebSocket hook**

Auto-reconnect, parse JSON messages, expose: `connected`, `matchState`, `turnLog`.

- [ ] **Step 3: Commit** — "feat: game types and WebSocket hook"

---

### Task 6.3: Battle UI Components

**Files:**
- Create: `frontend/src/components/BattleArena.tsx`
- Create: `frontend/src/components/FighterCard.tsx`
- Create: `frontend/src/components/ThoughtBubble.tsx`
- Create: `frontend/src/components/ActionLog.tsx`
- Create: `frontend/src/components/GameControls.tsx`

- [ ] **Step 1: Implement BattleArena** — grid with fighter positions (simple colored tiles)

- [ ] **Step 2: Implement FighterCard** — name, HP bar, energy bar, status effects

- [ ] **Step 3: Implement ThoughtBubble** — displays inner_monologue and trash_talk with typing animation

- [ ] **Step 4: Implement ActionLog** — scrolling list of turn events

- [ ] **Step 5: Implement GameControls** — start match button, fighter selection, mock/real toggle

- [ ] **Step 6: Wire everything together in App.tsx**

- [ ] **Step 7: Test end-to-end**: start backend, start frontend, run a mock match, verify UI updates

- [ ] **Step 8: Commit** — "feat: battle UI with arena grid, fighter cards, thought bubbles, action log"

---

## Phase 7: Polish & Ship

### Task 7.1: Docker Compose

- [ ] Create `Dockerfile` for backend
- [ ] Create `Dockerfile` for frontend
- [ ] Create `docker-compose.yml` that runs both + links them
- [ ] Verify `docker compose up` works end-to-end
- [ ] Commit — "feat: Docker setup for full stack"

### Task 7.2: End-to-End Real API Match

- [ ] Run a full GPT-4o vs Claude match through the web UI
- [ ] Screenshot/record for README
- [ ] Fix any issues discovered
- [ ] Update README with setup instructions and screenshots
- [ ] Commit — "docs: update README with setup instructions and demo"

### Task 7.3: Final Push

- [ ] All tests pass: `uv run pytest` and `pnpm test`
- [ ] Build succeeds: `pnpm build`
- [ ] Push to GitHub
- [ ] Tag v0.1.0

---

## Execution Notes

- **Phases 1-3 are the critical path.** After Phase 3, you have a working concept verification (CLI mock battles). Everything after is enhancement.
- **Phase 4 is the riskiest.** LLM prompt engineering will require iteration. Budget 2-3x the estimated time.
- **Phases 5-6 can be parallelized** — API server and frontend are independent until integration.
- **Phase 7 is polish** — only do this if Phases 1-6 are solid.

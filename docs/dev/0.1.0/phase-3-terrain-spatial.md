# Phase 3 — Terrain & Spatial Strategy

**Milestone:** v0.1.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 3`, `PRD §6`
**Prerequisites:** Phase 2 complete (archetype system working, status effects implemented)

---

## §1 Phase Goal & Purpose

Add terrain types to the arena so that **positioning creates real tactical decisions** every turn. Currently the grid is flat — moving has almost no strategic value. After this phase, terrain advantages (high ground range bonus, cover damage reduction) and terrain obstacles (rifts) make spatial reasoning a core skill the game evaluates.

**Why this matters:**
- Per `STRATEGY §2.3`, terrain and positioning must create real tradeoffs.
- Per `PRD §6`, the arena should reward range management, flanking, and routing decisions.
- Without terrain, "move left" and "move right" are equally meaningless. With terrain, every move is a tactical choice that spectators can evaluate.

---

## §2 Prerequisites & Dependencies

- Phase 2 complete: 4 archetypes working, status effects implemented, green tests.
- Understanding of `state.py` (Arena, Position, Hazard models), `combat.py` (damage calculation, movement), `game.py` (turn resolution).
- `PRD §6` for terrain type definitions and generation rules.

---

## §3 Execution Rules

### MUST DO

- Implement 3 terrain types per `PRD §6.1`:
  - **High Ground:** occupant gets +1 range on all abilities.
  - **Cover:** occupant takes -30% damage from ranged attacks (range > 2). Melee (range <= 2) is NOT reduced.
  - **Rift:** impassable tile. Movement into a rift is rejected (fighter stays in place).
- Implement symmetric terrain generation per `PRD §6.2`:
  - Random placement with a fixed seed (passed via `MatchConfig` or `Arena`).
  - Layout mirrored across the arena's vertical centerline (column 3.5 for an 8-wide grid). For each terrain tile placed at (x, y), a matching tile is placed at (7-x, y).
  - Terrain density: 15-25% of tiles (7-12 tiles on an 8x6 grid).
  - Both fighter starting positions must be on plain tiles.
- Implement ASCII grid generation per `PRD §6.3` for LLM prompt injection.
- Update `calculate_damage()` to check terrain at defender's position (Cover) and attacker's position (High Ground).
- Update `resolve_movement()` to reject movement into Rift tiles.
- Update `to_fighter_perspective()` to include the ASCII grid representation.
- Write tests for every terrain mechanic.
- All tests pass after changes.

### MUST NOT DO

- Do not change the prompt output format (Phase 4).
- Do not add turn history (Phase 4).
- Do not change CLI display beyond what is needed for terrain info (Phase 5).
- Do not add more than 3 terrain types.
- Do not add dynamic terrain (terrain that changes during a match). Terrain is static after generation.
- Do not add fog of war. Both fighters see the full grid.

---

## §4 Task Breakdown

### Task 3.1: Add Terrain Model to State

Extend `state.py`:

```python
class TerrainType(str, Enum):
    OPEN = "open"
    HIGH_GROUND = "high_ground"
    COVER = "cover"
    RIFT = "rift"
```

Add terrain data to `Arena`:
```python
class Arena(BaseModel):
    width: int = 8
    height: int = 6
    terrain: dict[str, str] = Field(default_factory=dict)
    # Key: "x,y" string, Value: TerrainType value
    # Tiles not in the dict are OPEN
    hazards: list[Hazard] = Field(default_factory=list)
```

Alternative: use `list[list[TerrainType]]` as a 2D grid. Choose whichever is simpler. The dict approach is sparser; the list approach is more explicit.

Add helper methods:
```python
def get_terrain_at(self, pos: Position) -> TerrainType:
    """Return terrain type at position. Defaults to OPEN."""

def is_passable(self, pos: Position) -> bool:
    """Return False if position is a Rift or out of bounds."""
```

### Task 3.2: Implement Terrain Generation

Add a `TerrainGenerator` class (can live in `combat.py` or a new `terrain.py` file in `engine/`):

```python
class TerrainGenerator:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def generate(self, arena: Arena, start_positions: list[Position]) -> None:
        """Populate arena.terrain with symmetric random placement."""
```

Generation algorithm:
1. Calculate target tile count: `rng.randint(7, 12)` for 8x6 grid.
2. Only place terrain on the left half (x < width // 2). For each placed tile, mirror it.
3. Terrain type distribution: ~40% High Ground, ~40% Cover, ~20% Rift.
4. Never place terrain on fighter starting positions.
5. Never place terrain on positions adjacent to starting positions (ensures fighters can move on turn 1).
6. Rifts should not create a wall that completely blocks crossing from left to right (basic connectivity check).

### Task 3.3: Integrate Terrain into Combat Resolver

Update `CombatResolver.calculate_damage()`:

```python
def calculate_damage(
    self,
    attacker: Fighter,
    defender: Fighter,
    ability: Ability,
    is_defending: bool,
    arena: Arena,  # NEW PARAMETER
) -> int:
```

Add two terrain checks after existing damage calculation:

1. **High Ground bonus (attacker):** If attacker is on High Ground, treat ability range as `range + 1` for the distance check. (This means the distance penalty threshold increases by 1, effectively extending range.)
2. **Cover reduction (defender):** If defender is on Cover AND the ability range > 2 (ranged attack), multiply damage by 0.7 (-30%).

**Important:** Update all call sites of `calculate_damage()` in `game.py` to pass the arena.

### Task 3.4: Update Movement for Rifts

Update `CombatResolver.resolve_movement()`:

```python
def resolve_movement(
    self,
    fighter: Fighter,
    direction: str | None,
    arena: Arena,  # Changed from width/height to Arena
) -> Position:
```

After calculating the new position, check `arena.is_passable(new_pos)`. If not passable, return the original position (movement rejected).

Update all call sites in `game.py`.

### Task 3.5: ASCII Grid Generation

Add a method to `Arena` or a utility function:

```python
def to_ascii_grid(self, fighters: list[Fighter]) -> str:
    """Generate ASCII representation of the arena for LLM prompts."""
```

Output format per `PRD §6.3`:
```
Arena (8x6):
  01234567
0 ........
1 ..H..C..
2 .##..##.
3 A......B
4 ..C..H..
5 ........

A=You  B=Opponent
H=High Ground  C=Cover  #=Rift  .=Open
Hazards: firewall@(3,1)[2t]
```

Rules:
- Fighter positions shown as A (current fighter) and B (opponent).
- Terrain symbols: H, C, #, . (period for open).
- Hazards listed below the grid (not overlaid — too confusing).
- Fighter symbols override terrain symbols at their positions.

### Task 3.6: Update `to_fighter_perspective()`

Add the ASCII grid to the battle state sent to LLMs. Add it as a `"arena_grid"` string field:

```python
def to_fighter_perspective(self, fighter_id: str) -> dict[str, Any]:
    # ... existing code ...
    return {
        # ... existing fields ...
        "arena_grid": self.arena.to_ascii_grid(
            fighters=[me, opponent],
            perspective_fighter_id=fighter_id,
        ),
    }
```

### Task 3.7: Update `_ensure_state()` in GameEngine

When initializing a match, generate terrain:

```python
def _ensure_state(self) -> None:
    # ... existing fighter setup ...
    arena = Arena()
    generator = TerrainGenerator(seed=self.config.seed)
    generator.generate(arena, start_positions=[f.position for f in fighters])
    self.state = BattleState(fighters=fighters, arena=arena, ...)
```

### Task 3.8: Update Hazard Spawning

Hazards should not spawn on Rift tiles (impassable). Update `CombatResolver.spawn_hazard()` to also check `arena.is_passable(pos)`.

### Task 3.9: Write Tests

- **Terrain model tests:** `TerrainType` enum, `get_terrain_at()`, `is_passable()`.
- **Generation tests:** symmetry verification, density range, starting position clearance, rift connectivity.
- **Combat tests:** High Ground +1 range, Cover -30% ranged damage, Cover no effect on melee.
- **Movement tests:** Rift blocks movement, normal terrain allows movement.
- **ASCII grid tests:** correct symbols, fighter position display, hazard listing.
- **Hazard tests:** no spawn on Rift.
- **Integration:** a turn where terrain modifies outcome.

### Task 3.10: Final Verification

Run full test suite. Run mock match and verify terrain appears in the ASCII grid output (check stdout or debug log).

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | 3 terrain types exist | Missing any type | High Ground, Cover, Rift all defined and functional |
| 2 | Terrain is symmetric | Left side != mirrored right side | Every terrain tile has a mirror counterpart |
| 3 | High Ground extends range | No range bonus on high ground | Attacker on HG gets +1 effective range |
| 4 | Cover reduces ranged damage | No damage reduction on cover | Defender on Cover takes -30% from ranged attacks |
| 5 | Cover does NOT reduce melee | Melee damage reduced on cover | Melee (range <= 2) ignores cover |
| 6 | Rifts block movement | Fighter can walk onto rift | Movement into rift is rejected |
| 7 | ASCII grid generated | No grid in prompt data | `to_fighter_perspective()` includes `arena_grid` string |
| 8 | Start positions clear | Fighter spawns on terrain | Both start positions are OPEN |
| 9 | Hazards respect terrain | Hazard spawns on rift | Hazards only spawn on passable tiles |
| 10 | All tests pass | Any failure | Full suite green |

---

## §6 Self-Audit Checklist

After completing all tasks:

- [ ] Place a fighter on High Ground, attack a distant target. Verify the +1 range bonus changes the outcome.
- [ ] Place a defender on Cover, attack from range 3+. Verify -30% damage reduction.
- [ ] Place a defender on Cover, attack from range 1. Verify NO damage reduction.
- [ ] Try to move a fighter onto a Rift tile. Verify movement is rejected.
- [ ] Generate 10 different terrains (different seeds). Verify all are symmetric.
- [ ] Check terrain density is in 15-25% range across multiple seeds.
- [ ] Verify no fighter starts on terrain.
- [ ] Print the ASCII grid. Does it look correct? Are fighters shown? Are hazards listed?
- [ ] `pytest -q` — all green.

---

## §7 Self-Optimization & Retry Guidance

**If terrain generation creates unreachable areas:**
- Add a simple flood-fill connectivity check. Both starting positions must be reachable from each other via passable tiles. If not, regenerate with a different seed offset.

**If the `calculate_damage()` signature change breaks many call sites:**
- Consider adding `arena` as an optional parameter with default `None`. When `None`, skip terrain checks. This minimizes test breakage while maintaining new functionality.

**If the ASCII grid is too token-heavy:**
- Measure the actual token count (use `tiktoken` or estimate 1 token per 4 chars). Target < 100 tokens. Reduce legend verbosity if needed.

**If terrain makes matches trivially one-sided:**
- This is a balance issue for Phase 6. Document the observation in the writeback. Do not tune terrain parameters in this phase unless the game is literally unplayable.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

**Completed by:** _(executor name/model)_
**Date:** _(date)_

**What was done:**

**What passed:**

**What failed or was unexpected:**

**Terrain generation stats (sample 10 seeds):**

**What changed from plan:**

**State left for Phase 4:**

---

## §9 Next Phase Pointer

**Next:** Phase 4 — Battle Memory & Prompt Contract (`docs/dev/0.1.0/phase-4-battle-memory-prompt.md`)

**What Phase 4 needs from this phase:**
- Working terrain system with 3 types.
- ASCII grid generation integrated into `to_fighter_perspective()`.
- Updated `calculate_damage()` accepting `arena` parameter.
- Green test suite.

**What Phase 4 does NOT need from this phase:**
- Terrain balance tuning (Phase 6).
- ASCII grid in the CLI display (Phase 5).
- Dynamic terrain or fog of war (out of scope).

# Phase 3 — Frontend Scaffold & Arena Renderer

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 3`
**Prerequisites:** Phase 2 complete (API server + WebSocket streaming working)

---

## §1 Phase Goal & Purpose

Bootstrap a React + TypeScript frontend app and build the core **arena grid renderer** — the single most important visual component in the entire project. After this phase, a browser can display a static battle state: the terrain grid, fighter positions, HP bars, and status effects.

**Why this matters:**
- The engine has been producing rich tactical data since v0.1.0. Zero humans have seen it outside a terminal. This phase creates the visual surface that makes the game **watchable** for a non-technical audience.
- The arena renderer is the foundation for everything in Phase 4 (animation) and Phase 5 (replays). Getting the spatial layout, terrain colors, and fighter representation right here avoids costly visual rework later.
- React + TypeScript + Vite is the pragmatic choice: fast dev server, strong typing for WebSocket messages, huge ecosystem for the animation/polish work in Phase 4.

---

## §2 Prerequisites & Dependencies

- Phase 2 complete: FastAPI server running at `localhost:8000`, REST and WebSocket endpoints working.
- Understanding of: arena grid dimensions (8x6), terrain types (open, high_ground, cover, rift), fighter state (HP, energy, position, status effects), archetype IDs.
- Node.js 20+ and npm/pnpm installed.

---

## §3 Execution Rules

### MUST DO

- Scaffold a React + TypeScript app with Vite in a top-level `frontend/` directory.
- Add CORS middleware to the FastAPI app so the frontend dev server (`localhost:5173`) can reach the API.
- Build these components:
  - **ArenaGrid** — 8x6 CSS Grid rendering terrain tiles with distinct colors/patterns.
  - **FighterToken** — fighter icon/indicator positioned on the grid.
  - **FighterPanel** — HP bar, energy bar, status effects, archetype name, model name.
  - **MatchLayout** — page layout with arena in center, fighter panels on sides.
- Use CSS Grid (not Canvas) for the arena. DOM-based rendering is simpler to iterate on and accessible.
- Define TypeScript types that mirror the backend Pydantic models (`BattleState`, `Fighter`, `TurnLog`, `Arena`, etc.).
- Render from static mock data first. Do NOT connect to WebSocket yet (Phase 4).
- Use a simple, dark-themed color palette appropriate for a fighting game.
- All existing backend tests must continue to pass.

### MUST NOT DO

- Do not use Canvas or WebGL. CSS Grid + DOM is sufficient for v0.2.0.
- Do not add animation or transitions yet (Phase 4).
- Do not connect to WebSocket yet (Phase 4).
- Do not add routing or multiple pages yet (Phase 5).
- Do not add a CSS framework (Tailwind, MUI, etc.) — raw CSS or CSS Modules to keep the bundle lean and the design intentional.
- Do not spend time on responsive design. Desktop-first (1280x720 minimum) is fine for v0.2.0.
- Do not add state management libraries (Redux, Zustand). React `useState`/`useReducer` is sufficient.

---

## §4 Task Breakdown

### Task 3.1: Scaffold Frontend App

```bash
cd "D:\Loster AI\Projects\LLM Smash Bros"
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm run dev  # verify it runs on localhost:5173
```

Clean up the Vite boilerplate: remove default logo, counter component, and CSS. Keep `App.tsx` as the root.

Project structure:
```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── types/           # TypeScript types mirroring backend models
│   │   └── game.ts
│   ├── components/
│   │   ├── ArenaGrid.tsx
│   │   ├── ArenaGrid.module.css
│   │   ├── FighterToken.tsx
│   │   ├── FighterToken.module.css
│   │   ├── FighterPanel.tsx
│   │   ├── FighterPanel.module.css
│   │   ├── MatchLayout.tsx
│   │   └── MatchLayout.module.css
│   ├── data/
│   │   └── mockState.ts  # static mock BattleState for development
│   └── styles/
│       └── global.css    # dark theme variables, reset
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Task 3.2: Define TypeScript Types

In `src/types/game.ts`, mirror the key backend models:

```typescript
export type TerrainType = "open" | "high_ground" | "cover" | "rift";

export interface Position {
  x: number;
  y: number;
}

export interface StatusEffect {
  type: string;
  value: number;
  remaining_turns: number;
}

export interface Ability {
  name: string;
  type: string;
  damage: number;
  energy_cost: number;
  range: number;
  cooldown: number;
  cooldown_remaining: number;
  description: string;
}

export interface Fighter {
  id: string;
  archetype: string;
  model_name: string;
  hp: number;
  max_hp: number;
  energy: number;
  max_energy: number;
  position: Position;
  status_effects: StatusEffect[];
  abilities: Ability[];
}

export interface Hazard {
  type: string;
  position: Position;
  damage: number;
  turns_remaining: number;
}

export interface Arena {
  width: number;
  height: number;
  terrain: Record<string, TerrainType>;  // "x,y" → terrain type
  hazards: Hazard[];
}

export interface BattleState {
  fighters: Fighter[];
  arena: Arena;
  turn_number: number;
  match_phase: string;
}

// WebSocket message types (for Phase 4, defined now for type safety)
export interface WsMatchStart {
  type: "match_start";
  match_id: string;
  fighters: Fighter[];
  arena: Arena;
}

export interface WsTurn {
  type: "turn";
  turn_number: number;
  turn_log: TurnLog;
}

export interface WsMatchEnd {
  type: "match_end";
  result: MatchResult;
}

export interface TurnLog {
  turn_number: number;
  actions: TurnAction[];
  events: TurnEvent[];
}

export interface TurnAction {
  fighter_id: string;
  action_type: string;
  ability?: string;
  move_direction?: string;
  tactical_summary?: string;
  trash_talk?: string;
}

export interface TurnEvent {
  type: string;
  description: string;
}

export interface MatchResult {
  winner: string | null;
  reason: string;
  total_turns: number;
}
```

### Task 3.3: Create Mock Battle State

In `src/data/mockState.ts`, create a realistic snapshot for visual development:

```typescript
import { BattleState } from "../types/game";

export const MOCK_STATE: BattleState = {
  turn_number: 12,
  match_phase: "fighting",
  fighters: [
    {
      id: "striker",
      archetype: "striker",
      model_name: "GPT-4o",
      hp: 52,
      max_hp: 80,
      energy: 35,
      max_energy: 60,
      position: { x: 2, y: 3 },
      status_effects: [{ type: "damage_boost", value: 1.3, remaining_turns: 2 }],
      abilities: [/* ... populate from roster.py ... */],
    },
    {
      id: "guardian",
      archetype: "guardian",
      model_name: "Claude Sonnet 4",
      hp: 78,
      max_hp: 120,
      energy: 15,
      max_energy: 40,
      position: { x: 5, y: 2 },
      status_effects: [],
      abilities: [/* ... */],
    },
  ],
  arena: {
    width: 8,
    height: 6,
    terrain: {
      "1,1": "high_ground",
      "6,1": "high_ground",
      "3,2": "cover",
      "4,2": "cover",
      "0,3": "rift",
      "7,3": "rift",
      "2,4": "cover",
      "5,4": "cover",
      "1,5": "high_ground",
      "6,5": "high_ground",
    },
    hazards: [
      { type: "firewall", position: { x: 4, y: 3 }, damage: 8, turns_remaining: 2 },
    ],
  },
};
```

### Task 3.4: Build ArenaGrid Component

The arena is an 8x6 grid. Each cell shows:
- Terrain type (background color/pattern)
- Fighter token (if a fighter is on this cell)
- Hazard indicator (if a hazard is on this cell)

```tsx
// ArenaGrid.tsx
interface ArenaGridProps {
  arena: Arena;
  fighters: Fighter[];
}

function ArenaGrid({ arena, fighters }: ArenaGridProps) {
  const cells = [];
  for (let y = 0; y < arena.height; y++) {
    for (let x = 0; x < arena.width; x++) {
      const terrain = arena.terrain[`${x},${y}`] || "open";
      const fighter = fighters.find(f => f.position.x === x && f.position.y === y);
      const hazard = arena.hazards.find(h => h.position.x === x && h.position.y === y);
      cells.push(
        <div key={`${x},${y}`} className={`cell cell--${terrain}`}>
          {hazard && <HazardIndicator hazard={hazard} />}
          {fighter && <FighterToken fighter={fighter} />}
        </div>
      );
    }
  }

  return (
    <div className="arena-grid" style={{
      display: "grid",
      gridTemplateColumns: `repeat(${arena.width}, 1fr)`,
      gridTemplateRows: `repeat(${arena.height}, 1fr)`,
    }}>
      {cells}
    </div>
  );
}
```

**Terrain color scheme (dark theme):**

| Terrain | Background | Border/Accent | Visual Metaphor |
|---------|-----------|---------------|-----------------|
| `open` | `#1a1a2e` (dark navy) | `#16213e` | Empty floor |
| `high_ground` | `#2d4a3e` (dark green) | `#4a7c59` | Elevated platform |
| `cover` | `#3a2a1a` (dark brown) | `#6b4c2a` | Barricade/wall |
| `rift` | `#0a0a0a` (near black) | `#8b0000` (dark red) | Impassable void |

Cell size: approximately 64x64px. Total arena: 512x384px.

### Task 3.5: Build FighterToken Component

A small, distinctive token rendered inside a grid cell:

```tsx
interface FighterTokenProps {
  fighter: Fighter;
}

function FighterToken({ fighter }: FighterTokenProps) {
  // Archetype-specific emoji or icon
  const archetypeIcons: Record<string, string> = {
    striker: "⚡",
    guardian: "🛡️",
    controller: "🎯",
    berserker: "🔥",
  };

  const hpPercent = (fighter.hp / fighter.max_hp) * 100;

  return (
    <div className={`fighter-token fighter-token--${fighter.archetype}`}>
      <span className="fighter-icon">{archetypeIcons[fighter.archetype]}</span>
      <div className="fighter-hp-mini" style={{ width: `${hpPercent}%` }} />
    </div>
  );
}
```

### Task 3.6: Build FighterPanel Component

Side panel showing detailed fighter status:

```
┌──────────────────────┐
│  ⚡ Striker           │
│  GPT-4o              │
│                      │
│  HP  ████████░░  65% │
│  EN  ██████░░░░  58% │
│                      │
│  Status: DMG BOOST   │
│          (2 turns)   │
│                      │
│  Abilities:          │
│  • Blitz Rush (rdy)  │
│  • Shadow Step (2cd) │
│  • Execution (rdy)   │
│  • Overdrive (5cd)   │
└──────────────────────┘
```

HP bar color: green > 50%, yellow 25-50%, red < 25%.
Energy bar color: blue gradient.
Status effects: colored badges.

### Task 3.7: Build MatchLayout Component

```
┌─────────────────────────────────────────────────┐
│                  LLM SMASH BROS                  │
│                   Turn 12 / 50                   │
├──────────┬─────────────────────┬────────────────┤
│          │                     │                │
│ Fighter1 │    Arena Grid       │ Fighter2       │
│  Panel   │    (8x6 grid)      │  Panel         │
│          │                     │                │
│          │                     │                │
├──────────┴─────────────────────┴────────────────┤
│              [Event log area]                    │
└─────────────────────────────────────────────────┘
```

### Task 3.8: Add CORS to FastAPI

In `app.py`, add CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(...)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite dev server
            "http://localhost:3000",   # Alternative
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")
    return app
```

### Task 3.9: Global Styles and Dark Theme

In `src/styles/global.css`:

```css
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent-red: #f85149;
  --accent-green: #3fb950;
  --accent-blue: #58a6ff;
  --accent-yellow: #d29922;
  --accent-purple: #bc8cff;

  --hp-high: #3fb950;
  --hp-mid: #d29922;
  --hp-low: #f85149;
  --energy-bar: #58a6ff;

  --terrain-open: #1a1a2e;
  --terrain-high-ground: #2d4a3e;
  --terrain-cover: #3a2a1a;
  --terrain-rift: #0a0a0a;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
```

### Task 3.10: Final Verification

```bash
# Frontend runs
cd frontend && npm run dev
# Open http://localhost:5173 — should see MatchLayout with mock data

# Backend still works
cd backend && uv run pytest -q
# 189+ tests pass

# CORS works
# From browser console on localhost:5173:
# fetch("http://localhost:8000/api/health").then(r => r.json()).then(console.log)
# Should return {"status": "ok"}
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Frontend app runs | `npm run dev` fails | Vite dev server starts, page loads in browser |
| 2 | Arena grid renders 8x6 | Grid is wrong size or missing | 48 cells visible with correct dimensions |
| 3 | Terrain colors are distinct | All tiles look the same | Each terrain type has a visually distinct color |
| 4 | Fighter tokens show on grid | Fighters not visible on arena | Two fighter tokens appear at correct positions |
| 5 | Fighter panels show stats | No HP/energy info visible | HP bar, energy bar, archetype, model name all displayed |
| 6 | HP bar reflects percentage | Bar doesn't change with HP | Bar width and color change based on HP percentage |
| 7 | Hazards visible on grid | Hazards invisible | Firewall/memory_leak indicators appear on correct tiles |
| 8 | Dark theme applied | White background or default Vite theme | Dark background, light text, fighting game aesthetic |
| 9 | CORS works | Frontend cannot reach API | `fetch("/api/health")` succeeds from frontend origin |
| 10 | Backend tests unbroken | Any backend test fails | All 189+ backend tests still pass |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Open the browser. Does the arena look like a fighting game, or like a spreadsheet?
- [ ] Can you tell which terrain type each cell is at a glance?
- [ ] Can you tell which fighter is which (archetype icon, panel position)?
- [ ] Is the HP bar color correct (green/yellow/red)?
- [ ] Does the layout work at 1280x720? (Resize browser window to check.)
- [ ] Is the mock data realistic? (Fighter positions on valid tiles, terrain is symmetric, etc.)
- [ ] Run backend tests. All green?

---

## §7 Self-Optimization & Retry Guidance

**If the arena looks cramped:**
- Increase cell size from 64px to 72px or 80px.
- Ensure the grid has adequate padding within the MatchLayout.

**If terrain colors are hard to distinguish:**
- Add a subtle pattern or icon to each terrain type in addition to color (e.g., rift gets diagonal stripes).
- Test with a screenshot color-blindness simulator.

**If CORS fails:**
- Check that `allow_origins` includes the exact origin (`http://localhost:5173` not `localhost:5173`).
- Check that the middleware is added BEFORE including routes.

**If TypeScript types drift from backend:**
- Consider auto-generating types from Pydantic schemas in a future phase. For now, manually sync is fine with 4 archetypes.

---

## §8 Execution Writeback

**What was done:**
- Scaffolded a Vite React + TS frontend app in `frontend/`.
- Added `CORSMiddleware` to `backend/src/llm_smash/api/app.py` so the frontend dev server can reach the API.
- Fixed a minor `pytest-asyncio` strictness issue on async fixtures in `test_api.py` that surfaced when running backend tests.
- Defined TS types `BattleState`, `Fighter`, `Arena`, `Ability`, `Hazard` etc. mirroring the backend models.
- Created `MOCK_STATE` populated with authentic `Striker` and `Guardian` data derived from `roster.py`.
- Implemented `ArenaGrid`, `FighterPanel`, `FighterToken`, and `MatchLayout` using pure CSS Modules and standard React, providing a distinct dark-theme fighting game aesthetic.
- Set up `global.css` with the specified layout attributes and color variables.

**What passed:**
- All 208 backend tests passed perfectly.
- The static layout renders correctly against the mock data.

**What changed from plan:**
- The backend `pytest` suite was throwing `pytest.PytestRemovedIn9Warning` as errors for using `@pytest.fixture` instead of `@pytest_asyncio.fixture` for the async `client` fixture, so `test_api.py` was updated to ensure tests pass on the latest environment.
- The UI components were structured to strictly follow the TDD design recommendations without deviating into complex CSS frameworks.

**Next phase starting point:**
- Proceed to Phase 4 (Live Battle Viewer) having a working DOM structure, TS types, CSS grid layout, and CORS-enabled API to wire up WebSockets.

---

## §9 Next Phase Pointer

**Next:** Phase 4 — Live Battle Viewer (`docs/dev/0.2.0/phase-4-live-battle-viewer.md`)

**What Phase 4 needs from this phase:**
- Working ArenaGrid, FighterToken, FighterPanel components that accept typed props.
- TypeScript types for WebSocket messages (already defined in `types/game.ts`).
- CORS configured so frontend can connect to backend.
- Dark theme and color palette established.

**What Phase 4 does NOT need from this phase:**
- WebSocket connection (Phase 4 wires it up).
- Animation or transitions (Phase 4).
- Routing or multiple pages (Phase 5).

# Phase 4 — Live Battle Viewer

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 4`
**Prerequisites:** Phase 3 complete (React app, ArenaGrid, FighterPanel, TypeScript types, CORS)

---

## §1 Phase Goal & Purpose

Wire the frontend to the WebSocket backend and bring the battle to life with **real-time turn updates, smooth transitions, and the dramatic rhythm of a fighting game**. After this phase, a user can click "Start Match," watch two AI fighters battle in real time, and see every turn resolve with visible intent, movement, damage, and trash talk.

**Why this matters:**
- This is the **money phase**. Everything before this was infrastructure. This is where the product goes from "works in terminal" to "looks like a game."
- The CLI experience proved the content is compelling. This phase proves the same content is compelling in a browser — the format that enables sharing, embedding, streaming, and viral spread.
- Per `STRATEGY §2.3`, strategy should be visible. Animated turn resolution with tactical summaries and trash talk is the maximum-visibility version of this principle.

---

## §2 Prerequisites & Dependencies

- Phase 3 complete: ArenaGrid, FighterToken, FighterPanel render correctly from mock data. TypeScript types defined. CORS working.
- Phase 2 backend: WebSocket streaming endpoint at `/api/matches/{id}/ws`. REST endpoint `POST /api/matches` creates matches.
- Understanding of: WebSocket message protocol (match_start, turn, match_end, state_sync), React state management, CSS transitions/animations.

---

## §3 Execution Rules

### MUST DO

- Build a `useMatchWebSocket` hook that connects to the backend WebSocket and dispatches state updates.
- Build a **MatchPage** component that shows the full live battle experience:
  - Match intro (fighter names, archetypes, model names).
  - Turn-by-turn updates: fighter tokens move on the grid, HP bars update, damage numbers flash, status effects appear/expire.
  - Tactical summary display per turn (what each fighter intended and why).
  - Trash talk display (shown briefly each turn, then faded or cycled).
  - Match conclusion: winner announcement, final stats.
- Add a **LobbyPage** component where users can:
  - Select archetypes for both fighters.
  - Choose mock mode (default) or enter API keys for live mode.
  - Click "Fight!" to start a match.
- Implement CSS transitions for state changes (HP bar width, fighter position, damage flash). NOT sprite animation or Canvas — CSS-only transitions are sufficient for v0.2.0.
- Add a turn pacing system: turns should render with a 1-2 second delay between them, even if the backend sends them faster. This creates readable rhythm.
- All existing backend tests must continue to pass.

### MUST NOT DO

- Do not use animation libraries (Framer Motion, GSAP, etc.) — raw CSS transitions only.
- Do not add sound effects or music (maybe v0.3.0).
- Do not add Canvas or WebGL rendering.
- Do not add routing (Phase 5 adds React Router for multi-page).
- Do not add spectator chat or audience interaction (v0.3.0).
- Do not implement API key management with secure storage — a simple text input that holds the key in component state is fine for v0.2.0.

---

## §4 Task Breakdown

### Task 4.1: Build useMatchWebSocket Hook

```typescript
// src/hooks/useMatchWebSocket.ts

interface UseMatchWebSocketReturn {
  status: "connecting" | "connected" | "disconnected" | "error";
  battleState: BattleState | null;
  turnLogs: TurnLog[];
  matchResult: MatchResult | null;
  currentTurn: TurnLog | null;
}

function useMatchWebSocket(matchId: string | null): UseMatchWebSocketReturn {
  // Connect to ws://localhost:8000/api/matches/{matchId}/ws
  // Handle message types: match_start, turn, match_end, state_sync
  // Update state via useReducer for complex state transitions
  // Auto-reconnect on disconnect (with backoff, max 3 attempts)
  // Cleanup WebSocket on unmount
}
```

**State management approach:**

Use `useReducer` with actions matching WebSocket message types:

```typescript
type MatchAction =
  | { type: "MATCH_START"; payload: WsMatchStart }
  | { type: "TURN"; payload: WsTurn }
  | { type: "MATCH_END"; payload: WsMatchEnd }
  | { type: "STATE_SYNC"; payload: WsStateSync }
  | { type: "CONNECTION_CHANGE"; status: string };
```

### Task 4.2: Build Turn Pacing Queue

The backend may send turns faster than humans can read. Implement a turn queue that renders turns with pacing:

```typescript
// src/hooks/useTurnPacer.ts

interface UseTurnPacerReturn {
  currentTurn: TurnLog | null;
  displayState: BattleState | null;
  isPaused: boolean;
  togglePause: () => void;
  skipToEnd: () => void;
}

function useTurnPacer(turnLogs: TurnLog[], paceMs: number = 1500): UseTurnPacerReturn {
  // Queue incoming turns
  // Dequeue and render one every `paceMs` milliseconds
  // Allow pause/resume and skip-to-end
  // Apply each turn's state changes to build displayState
}
```

Default pace: 1500ms per turn. This gives viewers time to read tactical summaries.

### Task 4.3: Build LobbyPage

```
┌─────────────────────────────────────────────────┐
│              LLM SMASH BROS                      │
│         "When LLMs stop benchmarking             │
│          and start brawling."                    │
│                                                  │
│  ┌──────────────┐    VS    ┌──────────────┐     │
│  │  Fighter 1   │          │  Fighter 2   │     │
│  │              │          │              │     │
│  │ [Striker  ▾] │          │ [Guardian ▾] │     │
│  │              │          │              │     │
│  │ Mode: Mock   │          │ Mode: Mock   │     │
│  └──────────────┘          └──────────────┘     │
│                                                  │
│              [ ⚔️ FIGHT! ]                       │
│                                                  │
└─────────────────────────────────────────────────┘
```

Components:
- Archetype selector (dropdown with the 4 archetypes).
- Mode toggle (mock / live). Live shows an API key input.
- "Fight!" button that POSTs to `/api/matches` and transitions to MatchPage.

### Task 4.4: Build MatchPage with Turn Display

The match page shows the live battle. Layout extends Phase 3's MatchLayout:

```
┌──────────────────────────────────────────────────┐
│  ⚡ Striker (GPT-4o)    Turn 12/50    🛡️ Guardian (Claude) │
├──────────┬─────────────────────┬─────────────────┤
│          │                     │                 │
│ Fighter1 │    Arena Grid       │ Fighter2        │
│  Panel   │   (animated)       │  Panel          │
│          │                     │                 │
├──────────┴─────────────────────┴─────────────────┤
│  Turn 12:                                         │
│  ⚡ Striker: "Closing distance for a Blitz Rush   │
│    while Guardian is low on energy."              │
│  💬 "Your loss function just yawned."             │
│                                                   │
│  🛡️ Guardian: "Defending on high ground to        │
│    absorb the incoming burst."                    │
│  💬 "I've processed bigger batches."              │
├───────────────────────────────────────────────────┤
│  [Pause ⏸] [Speed: Normal ▾] [Skip to End ⏭]    │
└───────────────────────────────────────────────────┘
```

### Task 4.5: Animate State Transitions

CSS transitions to add:

**Fighter movement:**
```css
.fighter-token {
  transition: transform 0.4s ease-out;
  /* Position via CSS Grid or absolute positioning within cell */
}
```

**HP bar changes:**
```css
.hp-bar-fill {
  transition: width 0.6s ease-out, background-color 0.6s ease;
}
```

**Damage flash:**
```css
.fighter-token--hit {
  animation: damage-flash 0.3s ease;
}
@keyframes damage-flash {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(2) saturate(0); }
}
```

**Damage numbers:**
```css
.damage-number {
  animation: float-up 1s ease-out forwards;
  color: var(--accent-red);
  font-weight: bold;
}
@keyframes float-up {
  0% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-30px); }
}
```

**Status effect badges:**
```css
.status-badge {
  animation: badge-appear 0.3s ease;
}
@keyframes badge-appear {
  from { transform: scale(0); }
  to { transform: scale(1); }
}
```

### Task 4.6: Match Intro and Conclusion Screens

**Intro (shown for 3 seconds before first turn):**
```
╔═══════════════════════════════════╗
║         MATCH START!              ║
║                                   ║
║  ⚡ Striker        🛡️ Guardian    ║
║     GPT-4o    VS    Claude 4      ║
║                                   ║
║     HP: 80         HP: 120        ║
║     "Speed kills"  "Patience wins"║
╚═══════════════════════════════════╝
```

**Conclusion (shown after match_end):**
```
╔═══════════════════════════════════╗
║          MATCH OVER!              ║
║                                   ║
║  🏆 WINNER: ⚡ Striker (GPT-4o)  ║
║     KO at Turn 34                 ║
║                                   ║
║  Total Turns: 34                  ║
║  Fumble Rate: 0%                  ║
║                                   ║
║  [Watch Replay]  [New Match]      ║
╚═══════════════════════════════════╝
```

### Task 4.7: Wire Everything Together in App.tsx

For v0.2.0 without React Router, use simple conditional rendering:

```tsx
function App() {
  const [view, setView] = useState<"lobby" | "match">("lobby");
  const [matchId, setMatchId] = useState<string | null>(null);

  if (view === "lobby") {
    return <LobbyPage onMatchStart={(id) => { setMatchId(id); setView("match"); }} />;
  }

  return <MatchPage matchId={matchId!} onBack={() => setView("lobby")} />;
}
```

### Task 4.8: Final Verification

```bash
# Backend running
cd backend && python -m llm_smash --serve &

# Frontend running
cd frontend && npm run dev

# Open browser:
# 1. See lobby page
# 2. Select Striker vs Guardian
# 3. Click "Fight!"
# 4. Watch match unfold turn by turn with transitions
# 5. See match result at the end
# 6. Click "New Match" to return to lobby

# Backend tests still pass
cd backend && uv run pytest -q
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | Lobby allows archetype selection | No way to choose fighters | Dropdowns for both fighter archetypes |
| 2 | "Fight!" starts a match | Button does nothing | POST to API, transitions to match view, WebSocket connects |
| 3 | Turns render in real time | All turns appear at once | Turns appear one by one with ~1.5s pacing |
| 4 | Fighter tokens move on grid | Tokens stay in place | Tokens animate to new positions each turn |
| 5 | HP bars update with transitions | HP bar jumps instantly | HP bar width transitions smoothly |
| 6 | Damage numbers appear | No damage feedback | Damage numbers float up from hit fighter |
| 7 | Tactical summaries display | No explanation of turns | Each fighter's tactical_summary shown per turn |
| 8 | Trash talk displays | No trash talk visible | Trash talk shown with distinct styling per turn |
| 9 | Match intro shows | Battle starts abruptly | 3-second intro screen with fighter info |
| 10 | Match conclusion shows | Match ends silently | Winner announcement with stats |
| 11 | Pause/resume works | No playback control | Pause button stops turn progression, resume continues |
| 12 | Backend tests unbroken | Any backend test fails | All 189+ backend tests still pass |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Watch a full mock match from lobby to conclusion. Is it **fun to watch**?
- [ ] Can you tell what each fighter did each turn? (tactical summary readable?)
- [ ] Is the pacing comfortable? Not too fast (can't read), not too slow (boring)?
- [ ] Do the transitions feel smooth or janky?
- [ ] Try pausing mid-match and resuming. Does it work?
- [ ] Try "Skip to End." Does it jump to the conclusion?
- [ ] Screenshot a mid-match frame. Would this look good as a tweet?
- [ ] Run backend tests. All green?

---

## §7 Self-Optimization & Retry Guidance

**If WebSocket doesn't connect:**
- Check CORS: WebSocket connections also need the origin allowed.
- Check the URL: `ws://localhost:8000/api/matches/{id}/ws` (not `wss://` for local dev).
- Check if the match exists by the time the WS connects. If the match finishes before connection, handle the `match_end` immediate response.

**If turns render too fast:**
- The turn pacer should queue incoming turns and dequeue them on a timer. If turns arrive in a burst (e.g., state_sync with 10 past turns), batch-apply them or skip to current state.

**If animations are janky:**
- Use `transform` and `opacity` for animations (GPU-accelerated), not `left`/`top`/`width`.
- Ensure transitions are on the correct properties and durations don't conflict.

**If the experience feels boring:**
- Increase visual drama: bigger damage numbers, more pronounced HP bar color transitions, screen shake on critical hits (CSS transform: translate with quick animation).

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

---

## §9 Next Phase Pointer

**Next:** Phase 5 — Replay Browser & Match History (`docs/dev/0.2.0/phase-5-replay-browser.md`)

**What Phase 5 needs from this phase:**
- Working live match viewer with all visual components.
- Turn pacing system that can be reused for replay playback.
- App.tsx structure that can be extended with routing.

**What Phase 5 does NOT need from this phase:**
- Replay playback from stored files (Phase 5 builds this).
- React Router (Phase 5 adds it).
- Match listing page (Phase 5).

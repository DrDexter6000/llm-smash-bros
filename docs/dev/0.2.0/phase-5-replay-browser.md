# Phase 5 — Replay Browser & Match History

**Milestone:** v0.2.0
**Status:** Not Started
**Authority:** `PLAN §4 Phase 5`
**Prerequisites:** Phase 4 complete (live battle viewer, turn pacer, lobby, WebSocket integration)

---

## §1 Phase Goal & Purpose

Add a match history page and replay playback system so users can **browse past matches and re-watch them**. This transforms ephemeral live matches into persistent, shareable content. After this phase, every match ever played is browsable, re-watchable, and linkable.

**Why this matters:**
- Live matches are exciting but transient. Without replays, the content value of a match ends when it finishes.
- Replays are the primary shareable asset: "watch this GPT-4o vs Claude fight" as a link is infinitely more viral than "trust me it was cool."
- The CLI already generates replay JSON files. This phase builds the viewer that makes them accessible.
- Match history enables pattern observation: "Claude always loses as Berserker" or "GPT-4o dominates mirror matches." These insights are the evaluation payload.

---

## §2 Prerequisites & Dependencies

- Phase 4 complete: MatchPage with turn pacer, ArenaGrid, FighterPanel, all visual components working for live matches.
- Phase 1-2 backend: `GET /api/matches` (list), `GET /api/matches/{id}/replay` (replay JSON).
- Understanding of: replay JSON format (from CLI's `save_replay()`), turn pacer from Phase 4 (reusable for replay playback).

---

## §3 Execution Rules

### MUST DO

- Add React Router for navigation between pages: Lobby (`/`), Live Match (`/match/:id`), Match History (`/history`), Replay (`/replay/:id`).
- Build a **MatchHistoryPage** that lists completed matches from the API with summary info (fighters, winner, turns, timestamp).
- Build a **ReplayPage** that loads a replay JSON and plays it back using the same visual components as the live viewer.
- Reuse the turn pacer from Phase 4 for replay playback.
- Add playback controls: play, pause, speed (0.5x, 1x, 2x, 4x), step forward, step backward, scrub bar.
- Add a replay file upload feature: users can drag-and-drop a CLI-generated replay JSON to watch it in the browser.
- Ensure replay URLs are shareable: `/replay/{match_id}` should load and play a specific replay.
- All existing backend tests must continue to pass.

### MUST NOT DO

- Do not add a database. In-memory match storage from Phase 1 is still the source.
- Do not add user accounts or authentication.
- Do not add social features (sharing, likes, comments).
- Do not add video export (GIF/MP4 generation is out of scope for v0.2.0).
- Do not add filtering by model or archetype beyond basic sorting (keep it simple).
- Do not break the existing live match flow.

---

## §4 Task Breakdown

### Task 5.1: Add React Router

```bash
cd frontend && npm install react-router-dom
```

Set up routes in `App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/match/:matchId" element={<MatchPage />} />
        <Route path="/history" element={<MatchHistoryPage />} />
        <Route path="/replay/:matchId" element={<ReplayPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

Update LobbyPage to navigate to `/match/:id` after creating a match.

### Task 5.2: Add Navigation Header

A minimal sticky header for page navigation:

```
┌──────────────────────────────────────────────┐
│  ⚔️ LLM Smash Bros    [New Match] [History]  │
└──────────────────────────────────────────────┘
```

Component: `NavBar.tsx` — always visible, links to `/` and `/history`.

### Task 5.3: Build MatchHistoryPage

```
┌──────────────────────────────────────────────────┐
│  Match History                                    │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ #abc123  ⚡Striker vs 🛡️Guardian            │  │
│  │ GPT-4o vs Claude 4  •  Winner: Striker     │  │
│  │ 34 turns  •  2 min ago                      │  │
│  │                          [Watch Replay →]   │  │
│  ├────────────────────────────────────────────┤  │
│  │ #def456  🔥Berserker vs 🎯Controller        │  │
│  │ Mock vs Mock  •  Winner: Controller         │  │
│  │ 28 turns  •  15 min ago                     │  │
│  │                          [Watch Replay →]   │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  [Load More]                                      │
└──────────────────────────────────────────────────┘
```

Fetch from `GET /api/matches` with pagination. Each card shows:
- Match ID (truncated)
- Fighter archetypes with icons
- Model names
- Winner
- Turn count
- Relative timestamp ("2 min ago")
- Link to `/replay/:matchId`

### Task 5.4: Build ReplayPage with Playback Controls

The ReplayPage loads a replay JSON from the API (`GET /api/matches/{id}/replay`) and renders it using the same MatchLayout, ArenaGrid, and FighterPanel components.

**Key difference from live MatchPage:** replay uses local data, not WebSocket.

```typescript
// src/hooks/useReplayPlayback.ts

interface UseReplayPlaybackReturn {
  currentTurn: number;
  totalTurns: number;
  displayState: BattleState;
  isPlaying: boolean;
  speed: number;
  play: () => void;
  pause: () => void;
  setSpeed: (speed: number) => void;
  stepForward: () => void;
  stepBackward: () => void;
  seekTo: (turn: number) => void;
}

function useReplayPlayback(replay: ReplayData): UseReplayPlaybackReturn {
  // Parse replay JSON into initial state + turn sequence
  // Maintain a "current turn" index
  // Apply turns sequentially to rebuild state at any point
  // Timer-based auto-advance when playing
  // Speed multiplier affects timer interval
}
```

**Playback control bar:**

```
┌────────────────────────────────────────────────┐
│  ⏮  ◀  ⏸/▶  ▶  ⏭   [====●==========] 12/34  │
│                        Speed: [0.5x] [1x] [2x] [4x] │
└────────────────────────────────────────────────┘
```

Controls:
- `⏮` — jump to start
- `◀` — step backward one turn
- `⏸/▶` — pause / play toggle
- `▶` — step forward one turn
- `⏭` — jump to end
- Scrub bar — drag to any turn
- Speed buttons — 0.5x, 1x, 2x, 4x

### Task 5.5: Replay File Upload

Add a drop zone to the LobbyPage or a dedicated `/upload` area:

```tsx
function ReplayUploader() {
  const handleDrop = (e: DragEvent) => {
    const file = e.dataTransfer.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      const replay = JSON.parse(reader.result as string);
      // Navigate to a local replay view with this data
    };
    reader.readAsText(file);
  };

  return (
    <div className="replay-drop-zone" onDrop={handleDrop} onDragOver={e => e.preventDefault()}>
      <p>Drop a replay JSON file here to watch it</p>
    </div>
  );
}
```

This enables users to play back replays generated by the CLI (`replays/` directory) without needing the API server.

### Task 5.6: Extract Shared Match Display Components

Refactor to avoid duplication between MatchPage (live) and ReplayPage (playback):

```
src/components/
├── match-display/
│   ├── MatchView.tsx       # Shared: arena + panels + turn info (accepts state as prop)
│   ├── TurnInfo.tsx         # Shared: tactical summary + trash talk
│   ├── PlaybackControls.tsx # Replay-only: scrub bar, speed, step
│   └── MatchIntro.tsx       # Shared: fighter intro screen
├── ArenaGrid.tsx            # Unchanged from Phase 3
├── FighterPanel.tsx         # Unchanged from Phase 3
└── FighterToken.tsx         # Unchanged from Phase 3
```

MatchPage and ReplayPage both render `<MatchView>` but feed it state from different sources (WebSocket vs replay file).

### Task 5.7: Final Verification

```bash
# Backend running
cd backend && python -m llm_smash --serve &

# Frontend running
cd frontend && npm run dev

# Test flow:
# 1. Start at / (lobby) → create a match → watch it live at /match/:id
# 2. After match ends, click "Watch Replay" or navigate to /history
# 3. History page shows the completed match
# 4. Click replay → /replay/:id plays back the match
# 5. Use playback controls: pause, step, speed, scrub
# 6. Back at lobby, drag-drop a CLI replay JSON → plays in browser

# Backend tests still pass
cd backend && uv run pytest -q
```

---

## §5 Acceptance Criteria

| # | Criterion | Red (Fail) | Green (Pass) |
|---|-----------|-----------|--------------|
| 1 | React Router works | No client-side navigation | `/`, `/match/:id`, `/history`, `/replay/:id` all render correct pages |
| 2 | Navigation header visible | No way to navigate between pages | NavBar with "New Match" and "History" links always visible |
| 3 | Match history lists matches | History page empty or broken | Completed matches shown with summary info |
| 4 | Replay playback works | Cannot re-watch a match | Replay renders turn-by-turn with same visuals as live |
| 5 | Playback controls work | No pause/speed/scrub | Play, pause, step, speed, and scrub bar all functional |
| 6 | Step backward works | Can only go forward | Step backward reconstructs previous turn state |
| 7 | Replay file upload works | No way to load local files | Drag-and-drop a CLI replay JSON → plays in browser |
| 8 | Live match flow unbroken | Phase 4 live viewer broken | Lobby → fight → live match still works end-to-end |
| 9 | URLs are shareable | Refreshing `/replay/:id` breaks | Direct navigation to `/replay/:id` loads and plays the replay |
| 10 | Backend tests unbroken | Any backend test fails | All 189+ backend tests still pass |

---

## §6 Self-Audit Checklist

After completing all tasks, verify:

- [ ] Complete a live match, then find it in history, then replay it. Full lifecycle works?
- [ ] Scrub the replay to turn 1, then to the last turn, then back to the middle. State correct each time?
- [ ] Speed up to 4x. Is it still readable?
- [ ] Open a CLI-generated replay JSON from `replays/` via drag-and-drop. Does it play?
- [ ] Refresh the browser on `/replay/:id`. Does it reload correctly?
- [ ] Try `/replay/nonexistent`. Does it show a "not found" message instead of crashing?
- [ ] Run backend tests. All green?

---

## §7 Self-Optimization & Retry Guidance

**If step backward is hard to implement:**
- The simplest approach: store the initial state + all turn deltas. To reach turn N, apply turns 1..N from initial state. This is O(N) per seek but trivially correct.
- Optimization (if needed): cache state snapshots every 10 turns. Seek to nearest cached snapshot, then apply remaining turns.

**If replay file format doesn't match API replay format:**
- CLI replay format (from `cli.py`) may differ from the API's `MatchResult.model_dump()`. Normalize both to a common `ReplayData` TypeScript type. Add a conversion function if needed.

**If routing breaks live match WebSocket:**
- Ensure the WebSocket connection is established after the component mounts, and cleaned up on unmount. React Router re-mounts components on navigation.

---

## §8 Execution Writeback

> *This section is filled by the executor after phase completion. Do not pre-fill.*

---

## §9 Next Phase Pointer

**Next:** Phase 6 — Integration, Polish & Deployment (`docs/dev/0.2.0/phase-6-integration-polish.md`)

**What Phase 6 needs from this phase:**
- Complete multi-page app with lobby, live match, history, and replay.
- Shared visual components that render consistently across live and replay modes.
- All routes working with direct URL navigation.

**What Phase 6 does NOT need from this phase:**
- Video/GIF export.
- Social features.
- Database persistence.

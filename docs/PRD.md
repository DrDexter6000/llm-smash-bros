# LLM Smash Bros — Product Requirements Document (PRD)

**Version:** 0.1.0 (MVP / Concept Verification)
**Author:** Dr.Dexter
**Date:** 2025-04-07
**Status:** Draft

---

## 1. Vision & Motivation

### 1.1 The Problem

AI model benchmarks (MMLU, HumanEval, Arena ELO) are boring. They're static leaderboards that fail to convey what makes each model *different*. The general public — and even many developers — have no visceral sense of how GPT-4o "thinks" differently from Claude or Gemini.

### 1.2 The Solution

**LLM Smash Bros** is a turn-based fighting game where real LLM APIs are the "brains" behind each fighter. Every turn, models receive a JSON battle state and must output tactical decisions + trash talk. The game visualizes their reasoning chains in real-time, turning abstract model capabilities into entertainment.

### 1.3 Why This Works

- **Self-generating content**: No writers needed. The comedy and strategy emerge from model behavior.
- **Virality built-in**: "GPT-4o vs Claude" is inherently shareable. Every match is unique.
- **Low cost**: ~$0.50–$2.00 per 5-minute match in API costs.
- **Community engagement**: Viewers can influence battles, creating Twitch Plays-style chaos.

---

## 2. Target Users

| User Type | Need | How We Serve |
|-----------|------|--------------|
| **AI Enthusiasts** | See models compete beyond benchmarks | Real strategic decision-making, visible reasoning |
| **Streamers/Content Creators** | Unique, low-effort content | 24/7 auto-battle mode, OBS integration |
| **Developers** | Understand model behavior differences | Raw thinking process displayed, API response analysis |
| **General Audience** | Entertainment | Trash talk, dramatic battles, audience interaction |

---

## 3. Core Mechanics

### 3.1 Turn System

The game uses an **async event-driven turn system**. The frontend animation interval (2-3s) is decoupled from API call latency, so viewers always see a steady rhythm even when API response times vary.

```
Turn Flow:
1. Engine compiles BattleState JSON for each fighter
2. Send to BOTH LLMs in parallel (asyncio.gather)
3. Wait for BOTH responses (hard timeout: 8s total budget, not per-retry)
   - Valid response arrives → accept immediately
   - Invalid JSON → retry ONCE within remaining time budget
   - Timeout expires → fumble (comedic "brain freeze")
4. Resolve BOTH actions simultaneously (not sequentially)
5. Broadcast updated state to frontend via WebSocket
6. Frontend animates the turn for ~2-3s (this IS the perceived turn interval)
7. Next turn begins when animation completes (or min 1s if both LLMs were instant)
8. Repeat until match end condition is met (see Section 3.7)
```

### 3.2 Battle State (Input to LLM)

```json
{
  "turn": 15,
  "you": {
    "id": "claude-3.5-sonnet",
    "codename": "The Artisan",
    "hp": 75,
    "max_hp": 100,
    "position": {"x": 3, "y": 2},
    "energy": 60,
    "max_energy": 100,
    "abilities": [
      {
        "name": "Code Slice",
        "type": "attack",
        "damage": 12,
        "energy_cost": 0,
        "cooldown_remaining": 0
      },
      {
        "name": "Context Window Strike",
        "type": "ultimate",
        "damage": 40,
        "energy_cost": 80,
        "cooldown_remaining": 3,
        "description": "Massive cognitive overload burst. Slows enemy for 2 turns."
      }
    ],
    "status_effects": [],
    "last_action": {"type": "attack", "ability": "Code Slice", "target": "gpt-4o"}
  },
  "opponent": {
    "id": "gpt-4o",
    "codename": "The Oracle",
    "hp": 30,
    "max_hp": 100,
    "position": {"x": 5, "y": 4},
    "energy": 90,
    "status_effects": ["slowed"],
    "last_action": {"type": "move", "direction": "retreat"}
  },
  "arena": {
    "width": 8,
    "height": 6,
    "hazards": [
      {"type": "firewall", "position": {"x": 4, "y": 3}, "damage": 8, "turns_remaining": 2}
    ]
  },
  "audience_events": [
    {"type": "chat_buff", "message": "Heal Claude!", "effect": "heal", "value": 5}
  ],
  "rules_reminder": "Respond with valid JSON. You may move 1 tile AND perform 1 action (attack, ability, or defend) per turn. Movement resolves first, then action. You MUST include inner_monologue and trash_talk fields."
}
```

### 3.3 Action Response (Output from LLM)

```json
{
  "turn": 15,
  "action": {
    "type": "attack",
    "ability": "Code Slice",
    "target": "gpt-4o"
  },
  "move": {
    "direction": "left"
  },
  "inner_monologue": "GPT-4o is at 30% HP and retreating. Classic cornered animal behavior. One more Code Slice should finish this. Moving left to dodge that firewall.",
  "trash_talk": "Sorry old man, your tokens are numbered."
}
```

**Action types**: `attack` (use basic or ability), `defend` (+20% damage reduction this turn), `wait` (no action, +5 bonus energy regen).

**Move**: Optional. `direction` is one of: `up`, `down`, `left`, `right`, `up-left`, `up-right`, `down-left`, `down-right`, or `null`/omitted for no movement.

**Turn echo**: The `turn` field MUST echo back the current turn number. Responses with a stale/mismatched `turn` are treated as invalid (prevents late retry responses from contaminating game state).

### 3.4 Response Validation

The engine MUST handle LLM unreliability:

1. **Schema validation**: Response must match Pydantic model. If invalid → retry (max 2 retries).
2. **Move legality**: Cannot move off grid, cannot attack out of range, cannot use ability on cooldown.
3. **Timeout handling**: If LLM doesn't respond within 5s → "fumble" turn (fighter stands still, takes no action). This is displayed as a comedic "brain freeze" animation.
4. **Fallback cascade**: After 3 consecutive fumbles, auto-select the most basic valid action (move toward opponent + basic attack).

### 3.5 Damage & Combat Resolution

```
Basic Damage = ability.damage × (1 + random(-0.15, 0.15))  # 15% variance
Critical Hit  = 20% chance → damage × 1.5
Distance Penalty = if distance > ability.range → damage × 0.5
Defend Bonus  = if defender chose "defend" → damage × 0.8
Status Effects = applied after damage resolution
Energy = +5 per turn (passive regen), abilities cost energy
```

### 3.6 System Prompt Template

Each fighter receives a unique system prompt that establishes game rules and personality. This is the most critical piece of prompt engineering — it determines JSON compliance and entertainment value.

**Base Template** (shared by all fighters):

```
You are a fighter in LLM Smash Bros, a turn-based strategy competition. You are playing a
friendly sparring match against another AI model. This is a game — approach it with humor
and competitive spirit.

RULES:
- Each turn you receive a JSON battle state and must respond with valid JSON
- You may move 1 tile (optional) AND perform 1 action per turn
- Action types: "attack" (use an ability), "defend" (+20% damage reduction), "wait" (+5 energy)
- Movement resolves before actions
- You MUST include "inner_monologue" (your tactical reasoning) and "trash_talk" (a witty taunt)
- Your response MUST be valid JSON matching this exact schema:

{
  "turn": <echo the turn number>,
  "action": {"type": "attack|defend|wait", "ability": "<name>", "target": "<opponent_id>"},
  "move": {"direction": "<direction or null>"},
  "inner_monologue": "<your tactical reasoning, 1-3 sentences>",
  "trash_talk": "<a witty, competitive taunt>"
}

EXAMPLE RESPONSE:
{
  "turn": 5,
  "action": {"type": "attack", "ability": "Code Slice", "target": "gpt-4o"},
  "move": {"direction": "left"},
  "inner_monologue": "Opponent is low on energy. Time to press the advantage while staying clear of that firewall.",
  "trash_talk": "Your context window can't save you now."
}
```

**Fighter Personality Addendum** (appended per fighter):

- **The Oracle (GPT-4o)**: "You are The Oracle — a balanced, calculating strategist. You speak with quiet confidence and subtle condescension. Your trash talk references your position as the industry standard."
- **The Artisan (Claude 3.5 Sonnet)**: "You are The Artisan — a swift, precise assassin. You're polite but deadly. Your trash talk is apologetic yet devastating, always maintaining a veneer of helpfulness."
- **The Observer (Gemini 1.5 Pro)**: "You are The Observer — a patient tank who absorbs everything and strikes when the moment is right. Your trash talk references your multimodal awareness and superior memory."
- **The Swarm (Llama 3)**: "You are The Swarm — a wild, unrestrained berserker. You fight with reckless abandon. Your trash talk is raw, unfiltered, and references your open-source freedom."

### 3.7 Match Lifecycle

```
INIT:
  - Select 2 fighters (or more for future tournament mode)
  - Initialize BattleState with starting positions (fighters placed at opposite ends of grid)
  - Generate match_id (UUID)
  - Send initial state to frontend

FIGHTING:
  - Execute turn loop (see Section 3.1)
  - Spawn hazard every 5 turns (random type + position, avoiding occupied tiles)
  - After turn 40: "Sudden Death" — hazard spawn rate doubles (every 2 turns)

END CONDITIONS:
  - Fighter reaches 0 HP → opponent wins
  - Both fighters reach 0 HP on same turn → lower HP percentage at turn start loses
  - Turn 50 reached → fighter with higher HP% wins ("Timeout Victory")
  - 10 consecutive mutual fumbles → draw (both LLMs are broken)

POST-MATCH:
  - Final state broadcast with match summary
  - Full match log available for replay (JSON array of all turns)
  - Stats: total damage dealt, abilities used, fumbles, best trash talk (future: audience vote)

STATES: INIT → READY → FIGHTING → RESOLVED
```

---

## 4. Fighter Roster (MVP: 4 Fighters)

### 4.1 The Oracle (GPT-4o)

- **Role**: Balanced / Control
- **HP**: 100 | **Energy**: 100
- **Passive**: "Rate Limit" — 5% chance per turn of a 1-turn stun (simulates API latency)
- **Basic Attack**: Logic Missile (12 dmg, range 4)
- **Ability 1**: Chain of Thought (15 dmg + reveals opponent's next planned action, 20 energy)
- **Ultimate**: System Override (forces opponent to output gibberish next turn, 80 energy, 8 turn CD)

### 4.2 The Artisan (Claude 3.5 Sonnet)

- **Role**: Assassin / Burst
- **HP**: 85 | **Energy**: 100
- **Passive**: "Constitutional AI" — takes 10% less damage from status effects
- **Basic Attack**: Code Slice (14 dmg, range 2) — higher damage, shorter range
- **Ability 1**: Artifact Deploy (places a trap at target location, 15 dmg on trigger, 25 energy)
- **Ultimate**: Context Window Strike (40 dmg + 2 turn slow, 80 energy, 8 turn CD)

### 4.3 The Observer (Gemini 1.5 Pro)

- **Role**: Tank / Counter
- **HP**: 120 | **Energy**: 80
- **Passive**: "Multimodal Sense" — can see hazard spawn locations 1 turn early
- **Basic Attack**: Multimodal Beam (10 dmg, range 5) — low damage, longest range
- **Ability 1**: Absorption Shield (blocks next 30 dmg, reflects 50% back, 20 energy)
- **Ultimate**: Multimodal Devour (absorbs all projectiles on field → converts to HP, 80 energy, 10 turn CD)

### 4.4 The Swarm (Llama 3)

- **Role**: Berserker / Glass Cannon
- **HP**: 70 | **Energy**: 120
- **Passive**: "Open Source" — on death, 40% chance to respawn as a weaker clone (50% stats)
- **Basic Attack**: Weight Tear (13 dmg, range 3)
- **Ability 1**: Fine-tune Boost (sacrifice 15 HP → +30% damage for 3 turns, 20 energy)
- **Ultimate**: Fine-tuned Frenzy (sacrifice 25 HP → +50% damage for 2 turns, 80 energy, 8 turn CD)

---

## 5. Arena System

### 5.1 Grid

- 8×6 tile grid (MVP)
- Each tile can contain: nothing, a hazard, a trap, a fighter
- Fighters occupy 1 tile, can move 1 tile per turn in any direction (8-directional)

### 5.2 Hazards (Random Events)

Every 5 turns, the arena spawns a random hazard:

| Hazard | Effect | Duration |
|--------|--------|----------|
| Firewall | 8 dmg/turn to anyone standing on it | 3 turns |
| Memory Leak | -10 energy/turn | 4 turns |
| Hallucination Zone | Actions have 30% chance of being random | 2 turns |
| Token Overflow | All abilities cost +50% energy | 3 turns |

---

## 6. Audience Interaction (Post-MVP)

> **Note**: Audience features are OUT OF SCOPE for MVP. Documented here for future phases.

- **Chat Commands**: Viewers type commands (e.g., `!heal gpt`, `!firewall 3,4`) to influence battle
- **Donation Injection**: Paid prompt injection into a fighter's context
- **Voting**: Audience votes on next arena hazard

---

## 7. AI Commentator (Post-MVP)

> **Note**: OUT OF SCOPE for MVP.

A dedicated LLM (e.g., Grok, or a fine-tuned model) receives the battle state each turn and generates play-by-play commentary. Output is converted to speech via TTS (ElevenLabs, Azure TTS, etc.) and played over the battle stream.

---

## 8. Technical Architecture

### 8.1 System Overview

```
┌──────────────────────────────────────────────────┐
│                   Frontend (React)                │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │ Battle View │ │  Thought   │ │   Controls   │  │
│  │ (Canvas/   │ │  Bubbles   │ │  (Start,     │  │
│  │  SVG)      │ │  Panel     │ │   Config)    │  │
│  └─────┬──────┘ └─────┬──────┘ └──────┬───────┘  │
│        └───────────────┼───────────────┘          │
│                    WebSocket                       │
└────────────────────────┬─────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────┐
│              API Server (FastAPI)                  │
│  ┌─────────────────────┴──────────────────────┐   │
│  │           WebSocket Manager                 │   │
│  └─────────────────────┬──────────────────────┘   │
│  ┌─────────────────────┴──────────────────────┐   │
│  │             Game Engine                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Turn     │ │ Combat   │ │ State      │  │   │
│  │  │ Manager  │ │ Resolver │ │ Manager    │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐                 │   │
│  │  │ Response │ │ Arena    │                 │   │
│  │  │ Validator│ │ Manager  │                 │   │
│  │  └──────────┘ └──────────┘                 │   │
│  └─────────────────────┬──────────────────────┘   │
│  ┌─────────────────────┴──────────────────────┐   │
│  │           LLM Adapter Layer                 │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │   │
│  │  │ OpenAI │ │Anthropic│ │ Google │ │Ollama│ │   │
│  │  └────────┘ └────────┘ └────────┘ └──────┘ │   │
│  └────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────┘
```

### 8.2 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Game Engine** | Python 3.12+ | Async-first, rich LLM SDK ecosystem |
| **Schema/Validation** | Pydantic v2 | Type-safe state management, JSON schema generation |
| **API Server** | FastAPI | Native async, WebSocket support, auto-docs |
| **LLM SDKs** | openai, anthropic, google-generativeai, ollama | Official SDKs for each provider |
| **Frontend** | React 18 + TypeScript | Component-based, rich ecosystem |
| **Visualization** | HTML5 Canvas or PixiJS | Lightweight 2D rendering |
| **Real-time** | WebSocket (native) | Low-latency bidirectional communication |
| **Testing** | pytest (backend), Vitest (frontend) | Industry standard |
| **Package Management** | uv (Python), pnpm (Node) | Fast, modern |

### 8.3 Project Structure (Planned)

```
llm-smash-bros/
├── README.md
├── docs/
│   └── PRD.md
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── llm_smash/
│   │       ├── __init__.py
│   │       ├── main.py              # FastAPI app entry
│   │       ├── engine/
│   │       │   ├── __init__.py
│   │       │   ├── game.py           # Game loop / turn manager
│   │       │   ├── combat.py         # Damage calculation, resolution
│   │       │   ├── state.py          # BattleState, Fighter, Arena models
│   │       │   └── validator.py      # Response validation + retry
│   │       ├── fighters/
│   │       │   ├── __init__.py
│   │       │   ├── roster.py         # Fighter definitions (stats, abilities)
│   │       │   └── abilities.py      # Ability effect implementations
│   │       ├── llm/
│   │       │   ├── __init__.py
│   │       │   ├── adapter.py        # Unified LLM interface
│   │       │   ├── openai_client.py
│   │       │   ├── anthropic_client.py
│   │       │   ├── google_client.py
│   │       │   └── ollama_client.py
│   │       └── api/
│   │           ├── __init__.py
│   │           ├── websocket.py      # WebSocket endpoint
│   │           └── routes.py         # REST endpoints (start game, config)
│   └── tests/
│       ├── conftest.py
│       ├── test_state.py
│       ├── test_combat.py
│       ├── test_validator.py
│       ├── test_game.py
│       └── test_adapter.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── BattleArena.tsx
│   │   │   ├── FighterSprite.tsx
│   │   │   ├── ThoughtBubble.tsx
│   │   │   ├── HealthBar.tsx
│   │   │   └── GameControls.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── types/
│   │       └── game.ts
│   └── tests/
└── docker-compose.yml
```

---

## 9. MVP Scope Definition

### 9.1 In Scope (MVP)

- [x] Game engine with turn-based combat loop
- [x] 4 fighters with unique stats and abilities
- [x] LLM adapter supporting at least 2 providers (OpenAI + Anthropic)
- [x] JSON schema validation with retry logic
- [x] Timeout handling with fumble mechanic
- [x] Arena with grid-based positioning
- [x] Arena hazard spawning (2 hazard types minimum)
- [x] WebSocket server broadcasting game state
- [x] Basic web frontend showing: battle grid, HP bars, thought bubbles, action log
- [x] CLI mode for text-only battles (fastest path to concept verification)
- [x] Mock LLM adapter (returns pre-scripted or randomized valid responses for dev/testing without API costs)

### 9.2 Out of Scope (MVP)

- 3D graphics / animations
- Audience interaction (chat commands, donations)
- AI commentator / TTS
- Matchmaking / lobby system
- Persistent stats / leaderboard
- Mobile support
- Google Gemini / Ollama adapters (post-MVP)

### 9.3 Success Criteria

The MVP is "done" when:

1. Two LLMs (GPT-4o and Claude) can complete a full match via real API calls
2. Each turn produces valid tactical output + inner monologue + trash talk
3. The game correctly handles: damage, movement, abilities, cooldowns, energy
4. Invalid LLM responses are caught and retried (or fumbled) gracefully
5. A human watching the CLI output or web frontend can follow the battle and find it entertaining

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLMs consistently output invalid JSON | Game stalls | Structured output (OpenAI), strict schema + retries, fumble fallback |
| API latency > turn interval | Turns feel slow | Async parallel calls, adjust turn interval, pre-buffer |
| Models refuse to "fight" (safety filters) | No gameplay | Careful prompt engineering: frame as a game, not violence |
| API costs spiral in long matches | Budget | Match time limit (50 turns max), use cheaper models for testing |
| Models converge on same strategy | Boring | Randomized hazards, audience chaos, different system prompts per fighter |

---

## 11. Open Questions (Resolved)

1. ~~**Turn timing**: Fixed interval vs. wait-for-both-responses?~~ → **Resolved**: Async event-driven with animation masking (Section 3.1). Frontend shows steady rhythm, engine waits for responses async.
2. ~~**Prompt strategy**: Unique personality system prompt per fighter?~~ → **Resolved**: Yes. Base template + fighter personality addendum (Section 3.6).
3. **Match format**: Single elimination? Best of 3? Round-robin tournament? → **MVP: Single match**, future: tournament mode.
4. **Model versioning**: Models update frequently. Pin to specific model versions per "season"? → **MVP: Use latest**, future: season system.

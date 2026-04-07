# LLM Smash Bros — Product Requirements Document (PRD)

**Version:** 0.4.0
**Last Updated:** 2026-04-07
**Authority:** Product-definition document; subordinate to `STRATEGY.md`, superior to `PLAN.md`
**Read after:** `STRATEGY.md`
**Read before:** `PLAN.md`

---

## 1. Product Vision

### 1.1 The Problem

AI leaderboards are informative but emotionally flat. They tell people which model scores higher, but not how different models behave under pressure, how they express tactical style, or whether they make readable strategic decisions in a dynamic environment.

### 1.2 The Product Promise

**LLM Smash Bros** is a spectator-first turn-based battle game where real LLMs pilot generic fighter archetypes on a fair, terrain-rich arena.

Per `STRATEGY §1`, the product goal is to make three things visible and entertaining:

1. **Tactical reasoning** — does the model understand terrain, range, energy, cooldowns, hazards, and timing?
2. **Strategic identity** — does each model develop a distinct play style even when given the same toolkit?
3. **Readable strategy** — can a viewer quickly understand why the model made a move?

### 1.3 What This Product Is Not

- Not a benchmark replacement.
- Not a combat simulator where fixed rules fully determine the fun.
- Not a raw chain-of-thought viewer.
- Not a model marketing exercise where fighter abilities mirror LLM brand positioning.

The product succeeds when a viewer can watch a match and say: **"I can tell how these models think differently, even with the same fighter."**

---

## 2. Product Principles

### 2.1 Fair Playground

Per `STRATEGY §2.1`, fighter archetypes are game characters independent of LLM identity. Any model can pilot any archetype. The arena tests decision quality, not brand flavor.

- Fighter identity comes from archetype design (stats, abilities, role).
- Model identity comes from the LLM piloting the fighter.
- A mirror match (same archetype, different models) is the purest evaluation.
- Cross-archetype matches test whether models can adapt to different toolkits.

### 2.2 Authenticity Over Illusion

- **Live mode** must use real LLM-generated battle decisions and taunts.
- **Mock mode** exists only for development, testing, and demo safety.
- The engine must never describe mechanics in prompts that are not implemented. Every ability and terrain effect the model reads about must work exactly as described.

### 2.3 Strategy Should Matter

- Match outcomes should reflect meaningful decisions, not just flavor text.
- Terrain, positioning, energy, cooldowns, and hazards must create real tradeoffs.
- Randomness may add drama, but it must not dominate perceived skill.

### 2.4 Spectator Readability

- Every turn should communicate: **what happened, why it happened, and what might happen next.**
- Persona and trash talk reinforce strategy rather than distract from it.
- Model reasoning is presented as short tactical summaries, not raw verbose transcripts.

---

## 3. Current Product Reality

### 3.1 Authentic Output Modes

- **Live mode:** real model output is sent by LLM adapters and parsed into game actions.
- **Mock mode:** uses scripted/randomized development text and actions for local testing.
- **Fumble fallback:** if a model times out or returns invalid output, the engine substitutes a hardcoded defensive fallback with an HP penalty.

### 3.2 Current Weaknesses (to be addressed in v0.1.0)

- Fighter roster is branded to specific LLMs instead of being generic archetypes.
- Several abilities describe effects (stun, slow, reflection, absorb) that are not implemented in the engine — the prompts lie to the models.
- Arena is a flat grid; movement has almost no tactical value.
- No turn history is provided to models; they cannot do multi-turn reasoning.
- `inner_monologue` field is debug-flavored, not spectator-readable.
- CLI uses raw ANSI codes with Windows compatibility issues.
- `__main__.py` has a duplicate code bug.

---

## 4. Core Experience Requirements

### 4.1 Match Loop

Each turn should feel like a mini drama beat:

1. Viewer sees the current battlefield with terrain.
2. Viewer understands each fighter's pressure and options.
3. Fighters "think" briefly.
4. Each fighter reveals a readable tactical intent.
5. Movement and action resolve, terrain effects apply.
6. Damage, status, and hazards update.
7. Viewer sees the new tactical situation.

### 4.2 What the Model Must Decide

For each turn, the model receives a structured battle state and must decide:

- whether to attack, defend, or wait
- which ability to use (considering energy, cooldowns, range)
- whether and where to move (considering terrain advantages)
- a short public tactical summary (1-2 sentences for spectator display)
- a trash talk line (in-character for the archetype)

### 4.3 What the Engine Must Resolve

The engine is responsible for deterministic and semi-random rule enforcement:

- action validation
- movement legality and terrain interaction
- damage calculation with terrain modifiers
- cooldown updates
- energy regeneration
- hazard spawning and effects
- status effect application and tick-down
- KO / timeout / draw rules

The viewer should understand that **models choose intent; the engine resolves consequences.**

---

## 5. Fighter Archetype Requirements

Per `STRATEGY §2.1`, fighter archetypes are generic game characters.

### 5.1 Archetype Design Rules

- Each archetype has a distinct combat role with real mechanical tradeoffs.
- Each archetype has exactly **4 abilities**: 1 basic (free), 2 tactical (medium cost, combo potential), 1 ultimate (high cost, long CD, high impact).
- Ability descriptions in prompts must exactly match engine behavior. No flavor-only effects.
- Archetype stats (HP, energy, move speed) must create meaningful asymmetry.

### 5.2 Target Archetypes (v0.1.0)

| Archetype | Role | HP | Energy | Design Intent |
|-----------|------|-----|--------|---------------|
| **Striker** | Burst / Assassin | Low | Medium | High risk, high reward. Close range burst. Rewards aggressive positioning. |
| **Guardian** | Tank / Control | High | Low | Absorbs damage, controls space. Rewards patience and positioning. |
| **Controller** | Range / Zoner | Medium | Medium | Maintains distance, area denial. Rewards terrain awareness and spacing. |
| **Berserker** | Glass Cannon / Momentum | Very Low | High | Self-damage for power. Rewards commitment and energy management. |

### 5.3 Archetype Balance Target

- No archetype should have a >60% win rate against any other in mirror-model matches.
- Each archetype should have at least one natural counter and one natural weakness.
- Win rate should correlate more with model decision quality than with archetype pick.

---

## 6. Terrain & Spatial Requirements

### 6.1 Terrain Types (v0.1.0)

The arena supports static terrain tiles generated at match start:

| Terrain | Mechanical Effect | Strategic Purpose |
|---------|-------------------|-------------------|
| **High Ground** | Occupant gets +1 range on all abilities | Rewards proactive positioning, creates contestable objectives |
| **Cover** | Occupant takes -30% ranged damage (not melee) | Creates defensive positions, encourages flanking |
| **Rift** | Impassable tile, blocks movement | Forces routing decisions, creates chokepoints |

### 6.2 Terrain Generation Rules

- Terrain layout is generated randomly at match start with a fixed seed (reproducible).
- Layout must be **symmetrically mirrored** across the arena centerline (fair for both sides).
- Terrain density: 15-25% of tiles are non-empty (enough to matter, not enough to clog).
- Both fighters start on plain tiles.

### 6.3 Arena Representation in Prompts

Terrain is communicated to models via an **ASCII grid** for token efficiency and spatial clarity:

```
Arena (8x6):
  01234567
0 ........
1 ..H..C..
2 .##..##.
3 ........
4 ..C..H..
5 ........

You[A]: (1,3)  Opponent[B]: (6,3)
Legend: H=High Ground  C=Cover  #=Rift  .=Open
Hazards: firewall@(3,1) [2 turns left]
```

This format costs ~60-80 tokens and provides direct spatial reasoning input.

---

## 7. Battle Memory & Prompt Contract

### 7.1 Turn History

Per `STRATEGY §3 Priority 4`, models receive a **structured summary of the last 3 turns** to enable multi-turn reasoning:

```json
"recent_turns": [
  {"turn": 10, "you": "attacked with Precision Cut -> 14 dmg", "opponent": "defended", "terrain": null},
  {"turn": 11, "you": "moved left, waited (+5 energy)", "opponent": "used Beam Strike -> 11 dmg to you", "terrain": "firewall spawned at (3,2)"},
  {"turn": 12, "you": "defended (-20% dmg)", "opponent": "moved right, missed (out of range)", "terrain": null}
]
```

Each turn summary is one-line per side. Total cost: ~100-150 tokens for 3 turns.

### 7.2 Public Reasoning Schema

Replace the current `inner_monologue` field with a structured `tactical_summary`:

```json
{
  "turn": 12,
  "action": {"type": "attack", "ability": "Precision Cut", "target": "opponent"},
  "move": {"direction": "up-left"},
  "tactical_summary": "Opponent is low HP and out of cover. Closing distance for the kill.",
  "trash_talk": "Your context window can't hold this L."
}
```

- `tactical_summary`: 1-2 sentences. What the fighter is trying to do and why. Designed for spectator display.
- `trash_talk`: in-character taunt. Humor layer.

### 7.3 Prompt Budget

Per `STRATEGY §4`, total prompt size must stay under **2000 tokens**:

| Component | Token Budget |
|-----------|-------------|
| System prompt (rules + archetype identity) | ~500 |
| Battle state JSON (current frame) | ~400 |
| ASCII arena grid | ~80 |
| Recent turns (3 turns) | ~150 |
| Rules reminder | ~80 |
| **Total** | **~1210** |

This leaves ~800 tokens of headroom for future expansion.

### 7.4 System Prompt Structure

The system prompt has three layers:

1. **Base Rules** (~300 tokens): game mechanics, action types, JSON format, critical constraints.
2. **Archetype Identity** (~150 tokens): role description, strategic philosophy, win condition, ideal patterns. This replaces the old LLM-branded personality prompts.
3. **Output Contract** (~50 tokens): exact JSON schema with field descriptions.

---

## 8. Fumble & Error Handling

### 8.1 Fumble Mechanics

When a model times out or produces invalid JSON:

- The fighter defaults to defend.
- The fighter takes an HP penalty: `max(1, max_hp // 10)`.
- A fumble event is logged with description.

### 8.2 Fumble as Content

Per community feedback, fumble presentation should be comedic:

- The raw invalid output (truncated to 100 chars) may be displayed as "cognitive breakdown gibberish" in the spectator UI.
- Fumble events should have entertaining descriptions (e.g., "The Striker's neural pathways short-circuit! Forced into defensive stance!").

---

## 9. User Types

| User Type | Need | Product Value |
|-----------|------|---------------|
| AI enthusiasts | Want to see models behave, not just rank | Tactical and stylistic contrast on a fair arena |
| Creators / streamers | Need entertaining autonomous content | Watchable battles with terminal aesthetic, OBS-ready |
| Developers | Want insight into model behavior under constraints | Structured reasoning, per-model fumble rates, replay data |
| General audience | Want spectacle and personality | Clear visuals, taunts, easy-to-follow strategy |

---

## 10. Success Criteria (v0.1.0)

The v0.1.0 milestone is complete when:

1. Fighter archetypes are generic and decoupled from LLM identity.
2. Terrain exists and creates meaningful positioning decisions.
3. Models receive turn history and produce spectator-readable tactical summaries.
4. A live match clearly uses real model-generated actions, not scripts.
5. The terminal output is polished enough to record/stream via OBS.
6. Every ability described in prompts has a working engine implementation.
7. Match outcomes feel driven more by tactical quality than by random variance or formatting failures.
8. Mirror matches (same archetype, different models) visibly showcase model differences.

---

## 11. Scope

### 11.1 In Scope for v0.1.0

- Generic archetype system with 4 balanced archetypes
- Terrain types (high ground, cover, rift) with symmetric generation
- Turn history injection (last 3 turns)
- Public reasoning schema (tactical_summary)
- Rich terminal CLI (OBS-streamable)
- Match replay serialization (JSON export)
- Status effect implementation (for abilities that reference them)
- Integration tests covering full match simulation

### 11.2 Out of Scope for v0.1.0

- Web GUI / animation layer
- API / WebSocket streaming
- Audience interaction
- AI commentator / TTS
- Tournament systems
- More than 4 archetypes
- More than 2 fighters per match

---

## 12. Risks

| Risk | Why It Matters | Mitigation |
|------|----------------|------------|
| Invalid model output dominates matches | Makes battles feel fake or broken | Strong validation, fumble comedy, prompt contract discipline |
| Prompt too complex for weak models | Excludes interesting contenders | Keep under 2000 token budget, test with small models |
| Terrain adds complexity without fun | Wasted effort | Start with 3 simple terrain types, validate before expanding |
| Archetype balance is off | One archetype dominates | Balance target in §5.3, batch-match analysis in Phase 6 |
| Mirror matches are boring | Reduces evaluation value | Ensure terrain randomness and hazard dynamics create variety |

---

## 13. Open Product Questions

1. What is the optimal number of recent turns to include (2? 3? 5?) for reasoning vs token cost?
2. Should terrain be fully visible to both players or include fog-of-war?
3. How should the CLI display terrain — pure ASCII or rich-formatted panels?
4. Should fumble gibberish display be opt-in or default?
5. What is the right balance between archetype asymmetry and mirror-match fairness?

---

## 14. Documentation Responsibility

If this file changes scope, product meaning, or success criteria, `PLAN.md` must be checked for contradictions in the same change.

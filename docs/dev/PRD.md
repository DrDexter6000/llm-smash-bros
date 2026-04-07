# LLM Smash Bros — Product Requirements Document (PRD)

**Version:** 0.3.0  
**Last Updated:** 2026-04-07  
**Authority:** Product-definition document; subordinate to `STRATEGY.md`, superior to `PLAN.md`  
**Read after:** `STRATEGY.md`  
**Read before:** `PLAN.md`

---

## 1. Product Vision

### 1.1 The Problem

AI leaderboards are informative but emotionally flat. They tell people which model scores higher, but not how different models behave under pressure, how they express style, or whether they make readable tactical decisions in a dynamic environment.

### 1.2 The Product Promise

**LLM Smash Bros** is a spectator-first turn-based battle game where real LLMs act as the brains of fighters.

Per `STRATEGY §1`, the product goal is not to expose raw chain-of-thought or obsess over provider plumbing. The goal is to make three things visible and entertaining:

1. **Tactical reasoning** — does the model understand range, energy, cooldowns, hazards, and timing?
2. **Persona** — does each model feel distinct in tone and play style?
3. **Readable strategy** — can a viewer quickly understand why the model made a move?

### 1.3 What This Product Is Not

- Not a benchmark replacement.
- Not a pure combat simulator where fixed rules fully determine the fun.
- Not a raw chain-of-thought viewer.
- Not a model configuration playground.

The product succeeds when a viewer can watch a match and say: **“I can tell how these models differ.”**

---

## 2. Product Principles

### 2.1 Authenticity Over Illusion

- **Live mode** must use real LLM-generated battle decisions and taunts.
- **Mock mode** exists only for development, testing, and demo safety.
- The product must clearly preserve this distinction in documentation and UX.

### 2.2 Spectator Readability Over Raw Verbosity

- The public-facing reasoning layer should be short, structured, and readable.
- Raw private reasoning should not be the UX goal.
- If the system keeps richer internal reasoning, the user should see only a curated tactical summary.

### 2.3 Strategy Should Matter

- Match outcomes should reflect meaningful decisions, not just flavor text.
- The game state must reward planning around positioning, energy, cooldowns, and hazards.
- Randomness may add drama, but it must not dominate perceived skill.

### 2.4 Entertainment Must Stay Legible

- Persona and trash talk matter, but they should reinforce strategy rather than distract from it.
- Every turn should communicate: **what happened, why it happened, and what might happen next.**

---

## 3. Current Product Reality

This section keeps the PRD grounded in current truth instead of drifting into fantasy.

### 3.1 Authentic Output Modes

- **Live mode:** real model output is sent by LLM adapters and parsed into game actions.
- **Mock mode:** uses scripted/randomized development text and actions for local testing.
- **Fumble fallback:** if a model times out or returns invalid output, the engine substitutes a hardcoded defensive fallback.

### 3.2 Current Strategy Surface

The current engine already allows meaningful tactical choices around:

- attack / defend / wait
- one-tile movement each turn
- energy management
- cooldown timing
- hazard avoidance
- range-aware decision-making

However, the current product still under-expresses:

- multi-turn planning
- opponent modeling
- readable strategic storytelling
- distinction between private reasoning and public explanation

### 3.3 Current Viewer Experience

The CLI proves the game loop works, but it is still primarily an engineering-facing surface. It does not yet deliver the intended spectator-grade presentation of model strategy.

---

## 4. Core Experience Requirements

### 4.1 Match Loop

Each turn should feel like a mini drama beat:

1. Viewer sees the current battlefield.
2. Viewer understands each fighter’s pressure and options.
3. Fighters “think” briefly.
4. Each fighter reveals a readable strategic intent.
5. Movement and action resolve.
6. Damage, status, and hazards update.
7. Viewer sees the new tactical situation.

**Implemented by:** `PLAN §5 Phase E`

### 4.2 What the Model Must Decide

For each turn, the model must decide:

- whether to attack, defend, or wait
- which ability to use
- whether and where to move
- how to express short-form public strategy
- how to express persona through trash talk

### 4.3 What the Engine Must Resolve

The engine is responsible for deterministic and semi-random rule enforcement, including:

- action validation
- movement legality
- damage calculation
- cooldown updates
- energy regeneration
- hazard spawning and hazard effects
- KO / timeout / draw rules

The viewer should understand that **models choose intent; the engine resolves consequences.**

---

## 5. Public Reasoning Requirement

### 5.1 Current State

The current output contract includes an `inner_monologue` text field. This is useful for debugging and early flavor, but it is not yet the right long-term spectator-facing format.

### 5.2 Target State

Per `STRATEGY §3 Priority 1`, the public reasoning layer should evolve into a short, structured explanation that is easy to animate and display. It should answer:

- **Situation:** what does the fighter believe is happening?
- **Intent:** what is it trying to do this turn?
- **Key factor:** what tactical factor mattered most?
- **Risk:** what could go wrong?

**Implemented by:** `PLAN §5 Phase C`

### 5.3 UX Requirement

This reasoning should be readable in 1–3 seconds by a spectator. It should feel like tactical commentary, not a raw transcript dump.

---

## 6. Gameplay Requirements

### 6.1 Tactical Depth Requirements

The game should reward:

- range management
- positioning
- cooldown timing
- energy conservation and spending
- hazard awareness
- opportunistic aggression vs defensive patience

**Implemented by:** `PLAN §5 Phase D`

### 6.2 Balance Requirements

- Randomness can create drama, but should not overwhelm decision quality.
- Fighter kits should create real tradeoffs rather than superficial flavor differences.
- Distinct model personas should correspond to distinct tactical incentives where possible.

### 6.3 Match Interpretability

After a match, a viewer should be able to explain:

- why the winner won
- which tactical choices mattered most
- whether the match felt skill-driven, luck-driven, or failure-driven

---

## 7. Fighter Identity Requirements

Each fighter must have a recognizable combination of:

- role in combat
- ability profile
- personality and voice
- strategic tendency

The roster should not just be different names pasted onto similar kits. Identity must show up in both **battle decisions** and **presentation layer**.

---

## 8. User Types

| User Type | Need | Product Value |
|---|---|---|
| AI enthusiasts | Want to see models behave, not just rank | Tactical and stylistic contrast between fighters |
| creators / streamers | Need entertaining autonomous content | Watchable battles with readable dramatic beats |
| developers | Want insight into model behavior under constraints | Structured reasoning and turn-by-turn tactical evidence |
| general audience | Want spectacle and personality | Clear visuals, taunts, and easy-to-follow strategy |

---

## 9. Scope

### 9.1 In Scope Now

- Real LLM-driven turn selection in live mode
- Mock mode for development and testing
- Turn-based combat with positioning, abilities, energy, cooldowns, and hazards
- CLI proof of concept
- Structured output validation and fumble handling

### 9.2 Next In Scope

- spectator-grade public reasoning format
- richer battle-state that rewards deeper strategy
- GUI/animation layer that exposes strategy as a dynamic experience
- balancing work to reduce randomness-vs-skill ambiguity

### 9.3 Out of Scope for Near Term

- raw chain-of-thought display as a core feature
- broad audience interaction systems
- AI commentator / TTS
- tournament ecosystem / leaderboard meta
- deployment polish before spectator experience is convincing

---

## 10. Success Criteria

The next meaningful product milestone is reached when:

1. A live match clearly uses real model-generated actions and flavor.
2. A viewer can understand each turn’s tactical intention without reading raw verbose reasoning.
3. Different fighters feel meaningfully distinct in both play style and voice.
4. Match outcomes feel driven more by tactical quality than by random variance or formatting failures.
5. The project is interesting as a spectator product, not just as an engineering demo.

**Driven by:** `PLAN §7`

---

## 11. Risks

| Risk | Why It Matters | Mitigation Direction |
|---|---|---|
| Invalid model output dominates matches | Makes battles feel fake or broken | Strong validation, recovery, and better prompt contracts |
| Raw reasoning is too long or messy | Hurts UX and readability | Structured public reasoning layer |
| Randomness obscures skill | Weakens the core promise | Rebalance combat math and analyze match outcomes |
| Fighters feel cosmetically different only | Low replay value | Align kits, prompts, and display with strategic identity |
| Product focus drifts back to plumbing | Slows actual product progress | Use strategy snapshot and roadmap discipline |

---

## 12. Open Product Questions

1. What exact public reasoning schema is most watchable?
2. How much randomness is enough for drama without burying skill?
3. Which battle-state additions best encourage multi-turn planning?
4. What is the minimum GUI needed to make the product feel spectator-ready?
5. How should we communicate live-vs-mock authenticity in the UI?

---

## 13. Documentation Responsibility

If this file changes scope, product meaning, or success criteria, `PLAN.md` must be checked for contradictions in the same change.

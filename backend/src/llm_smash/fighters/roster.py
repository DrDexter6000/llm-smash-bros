"""Fighter roster definitions for LLM Smash Bros.

All 4 fighters with their stats, abilities, and system prompt personalities
as defined in PRD Sections 4 and 3.6.
"""

from __future__ import annotations

from llm_smash.engine.state import Ability, Fighter, Position

FIGHTER_IDS = ["gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro", "llama-3"]

# --- System Prompt Templates (PRD Section 3.6) ---

BASE_SYSTEM_PROMPT = """You are a fighter in LLM Smash Bros, a turn-based strategy competition against another AI model.
This is a game — approach it with humor and competitive spirit.

RULES:
- Each turn you receive a JSON battle state and MUST respond with ONLY a JSON object (no markdown, no explanation).
- You may move 1 tile (optional) AND perform 1 action per turn.
- Action types: "attack" (use an ability by name), "defend" (+20% damage reduction), "wait" (+5 energy regen).
- Movement resolves BEFORE actions. Use movement to get in range or dodge hazards.
- Attacks require enough energy AND the target must be within the ability's range.
- If an ability has cooldown_remaining > 0, it is NOT available this turn.

TACTICAL TIPS:
- Check your "abilities" list in the state — use the EXACT ability name in your response.
- Check "energy" — if you can't afford an ability, use "wait" to regen or "defend" to reduce incoming damage.
- Check distance to opponent: |your_x - opp_x| + |your_y - opp_y| = Manhattan distance. Must be <= ability range to hit.
- "defend" is better than a wasted attack. "wait" when low on energy.
- Watch for arena hazards — they hurt if you stand on them.

RESPONSE FORMAT — respond with ONLY this JSON object, nothing else:
{
  "turn": <echo the turn number from the state>,
  "action": {"type": "attack", "ability": "<exact ability name>", "target": "<opponent id>"},
  "move": {"direction": "<up|down|left|right|up-left|up-right|down-left|down-right>" or null},
  "inner_monologue": "<your tactical reasoning, 1-3 sentences>",
  "trash_talk": "<a witty, competitive taunt>"
}

For defend/wait, omit "ability" and "target":
{"type": "defend"} or {"type": "wait"}

Valid directions: up, down, left, right, up-left, up-right, down-left, down-right, or null for staying put.

CRITICAL: Output ONLY the raw JSON object. No markdown fences, no explanation, no extra text.
"""

PERSONALITY_PROMPTS: dict[str, str] = {
    "gpt-4o": (
        "You are The Oracle — a balanced, calculating strategist. You speak with quiet "
        "confidence and subtle condescension. Your trash talk references your position as "
        "the industry standard. You analyze patterns meticulously and always have a backup plan."
    ),
    "claude-3.5-sonnet": (
        "You are The Artisan — a swift, precise assassin. You're polite but deadly. Your "
        "trash talk is apologetic yet devastating, always maintaining a veneer of helpfulness. "
        "You favor aggressive close-range combat and calculated risks."
    ),
    "gemini-1.5-pro": (
        "You are The Observer — a patient tank who absorbs everything and strikes when the "
        "moment is right. Your trash talk references your multimodal awareness and superior "
        "memory. You prefer to control space and outlast your opponent."
    ),
    "llama-3": (
        "You are The Swarm — a wild, unrestrained berserker. You fight with reckless "
        "abandon. Your trash talk is raw, unfiltered, and references your open-source "
        "freedom. You believe in overwhelming force over careful planning."
    ),
}


def get_system_prompt(fighter_id: str) -> str:
    """Get the full system prompt for a fighter (base rules + personality)."""
    personality = PERSONALITY_PROMPTS.get(
        fighter_id, "You are a mysterious challenger."
    )
    return f"{BASE_SYSTEM_PROMPT}\n\n{personality}"


# --- Fighter Definitions (PRD Section 4) ---


def _create_oracle() -> Fighter:
    """GPT-4o: The Oracle — Balanced / Control."""
    return Fighter(
        id="gpt-4o",
        codename="The Oracle",
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Logic Missile",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=4,
                description="A precise beam of logical reasoning.",
            ),
            Ability(
                name="Chain of Thought",
                type="attack",
                damage=15,
                energy_cost=20,
                cooldown=0,
                cooldown_remaining=0,
                range=4,
                description="A deep chain of reasoning strikes for 15 damage.",
            ),
            Ability(
                name="System Override",
                type="ultimate",
                damage=30,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=6,
                description="Overrides all logic circuits for 30 damage. Long range, high cost.",
            ),
        ],
    )


def _create_artisan() -> Fighter:
    """Claude 3.5 Sonnet: The Artisan — Assassin / Burst."""
    return Fighter(
        id="claude-3.5-sonnet",
        codename="The Artisan",
        hp=85,
        max_hp=85,
        energy=100,
        max_energy=100,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Code Slice",
                type="attack",
                damage=14,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
                description="A sharp cut of optimized code. High damage, short range.",
            ),
            Ability(
                name="Artifact Deploy",
                type="attack",
                damage=15,
                energy_cost=25,
                cooldown=0,
                cooldown_remaining=0,
                range=3,
                description="Deploys an artifact strike for 15 damage at medium range.",
            ),
            Ability(
                name="Context Window Strike",
                type="ultimate",
                damage=40,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=3,
                description="Massive cognitive overload burst for 40 damage. High cost, long cooldown.",
            ),
        ],
    )


def _create_observer() -> Fighter:
    """Gemini 1.5 Pro: The Observer — Tank / Counter."""
    return Fighter(
        id="gemini-1.5-pro",
        codename="The Observer",
        hp=120,
        max_hp=120,
        energy=80,
        max_energy=80,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Multimodal Beam",
                type="attack",
                damage=10,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=5,
                description="Low damage beam with longest range.",
            ),
            Ability(
                name="Absorption Shield",
                type="attack",
                damage=8,
                energy_cost=20,
                cooldown=0,
                cooldown_remaining=0,
                range=0,
                description="Absorbs ambient energy and redirects it for 8 damage. No movement required.",
            ),
            Ability(
                name="Multimodal Devour",
                type="ultimate",
                damage=35,
                energy_cost=80,
                cooldown=10,
                cooldown_remaining=0,
                range=6,
                description="Devours all data streams for 35 damage. Long range, high cost.",
            ),
        ],
    )


def _create_swarm() -> Fighter:
    """Llama 3: The Swarm — Berserker / Glass Cannon."""
    return Fighter(
        id="llama-3",
        codename="The Swarm",
        hp=70,
        max_hp=70,
        energy=120,
        max_energy=120,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Weight Tear",
                type="attack",
                damage=13,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=3,
                description="A savage tear through neural weights.",
            ),
            Ability(
                name="Fine-tune Boost",
                type="attack",
                damage=10,
                energy_cost=20,
                cooldown=0,
                cooldown_remaining=0,
                range=3,
                description="A tuned weight adjustment strikes for 10 damage.",
            ),
            Ability(
                name="Fine-tuned Frenzy",
                type="ultimate",
                damage=35,
                energy_cost=80,
                cooldown=8,
                cooldown_remaining=0,
                range=3,
                description="Unleashes all fine-tuned weights for 35 damage. High cost, devastating.",
            ),
        ],
    )


_FIGHTER_FACTORY = {
    "gpt-4o": _create_oracle,
    "claude-3.5-sonnet": _create_artisan,
    "gemini-1.5-pro": _create_observer,
    "llama-3": _create_swarm,
}


def get_fighter(fighter_id: str) -> Fighter:
    """Get a fresh fighter instance by ID.

    Raises ValueError if the fighter ID is unknown.
    """
    factory = _FIGHTER_FACTORY.get(fighter_id)
    if factory is None:
        raise ValueError(
            f"Unknown fighter ID: '{fighter_id}'. "
            f"Available fighters: {', '.join(FIGHTER_IDS)}"
        )
    return factory()


def get_all_fighters() -> list[Fighter]:
    """Get fresh instances of all fighters in the roster."""
    return [get_fighter(fid) for fid in FIGHTER_IDS]

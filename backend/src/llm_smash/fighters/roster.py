"""Archetype roster definitions for LLM Smash Bros."""

from __future__ import annotations

from llm_smash.engine.state import Ability, AbilityEffect, Fighter, Position

ARCHETYPE_IDS = ["striker", "guardian", "controller", "berserker"]
FIGHTER_IDS = ARCHETYPE_IDS

BASE_SYSTEM_PROMPT = """You are a fighter in LLM Smash Bros, a turn-based strategy competition against another AI model.
This is a game — approach it with humor and competitive spirit.

RULES:
- Each turn you receive a JSON battle state and MUST respond with ONLY a JSON object (no markdown, no explanation).
- You may move 1 tile (optional) AND perform 1 action per turn.
- Action types: "attack" (use an ability by name), "defend" (+20% damage reduction), "wait" (+5 energy regen).
- Movement resolves BEFORE actions. Use movement to get in range or dodge hazards.
- Attacks require enough energy AND the target must be within the ability's range.
- If an ability has cooldown_remaining > 0, it is NOT available this turn.
- Status effects are real: stun skips your action, slow blocks movement, damage_boost increases outgoing damage, and damage_reduction cuts incoming damage.

TACTICAL TIPS:
- Check your "abilities" list in the state — use the EXACT ability name in your response.
- Check "energy" — if you can't afford an ability, use "wait" to regen or "defend" to reduce incoming damage.
- Check distance to opponent: max(|your_x - opp_x|, |your_y - opp_y|) = grid distance. Must be <= ability range to hit at full power.
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

ARCHETYPE_PROMPTS: dict[str, str] = {
    "striker": (
        "ARCHETYPE: Striker (Burst / Assassin)\n"
        "YOUR WIN CONDITION: Close distance, deliver burst damage, retreat to recover.\n"
        "YOUR STRENGTHS: High damage, mobility. YOUR WEAKNESSES: Low HP, short range.\n"
        "IDEAL PATTERN: Approach → burst → retreat → recover energy → repeat.\n"
        "PERSONALITY: Aggressive, confident, taunts about speed and precision."
    ),
    "guardian": (
        "ARCHETYPE: Guardian (Tank / Control)\n"
        "YOUR WIN CONDITION: Outlast the opponent, blunt their offense, and punish greedy plays.\n"
        "YOUR STRENGTHS: High HP, defensive tools, control. YOUR WEAKNESSES: Low energy, limited burst.\n"
        "IDEAL PATTERN: Hold ground → fortify → punish overextension → close with control.\n"
        "PERSONALITY: Stoic, immovable, taunts about discipline and inevitability."
    ),
    "controller": (
        "ARCHETYPE: Controller (Range / Zoner)\n"
        "YOUR WIN CONDITION: Keep distance, chip safely, and ruin the opponent's positioning.\n"
        "YOUR STRENGTHS: Long range, spacing, knockback. YOUR WEAKNESSES: Lower durability up close.\n"
        "IDEAL PATTERN: Kite → poke → deny space → finish from range.\n"
        "PERSONALITY: Cold, cerebral, taunts about superior battlefield control."
    ),
    "berserker": (
        "ARCHETYPE: Berserker (Glass Cannon / Momentum)\n"
        "YOUR WIN CONDITION: Spend HP like fuel, snowball damage, and end the fight before your body gives out.\n"
        "YOUR STRENGTHS: Huge burst, high energy, momentum. YOUR WEAKNESSES: Fragile HP, self-damage.\n"
        "IDEAL PATTERN: Buff → commit hard → force panic → finish before collapse.\n"
        "PERSONALITY: Feral, reckless, taunts about raw aggression and unstoppable pressure."
    ),
}


def get_system_prompt(fighter_id: str) -> str:
    """Get the full system prompt for an archetype."""
    personality = ARCHETYPE_PROMPTS.get(fighter_id, "You are a mysterious challenger.")
    return f"{BASE_SYSTEM_PROMPT}\n\n{personality}"


def _create_striker() -> Fighter:
    return Fighter(
        id="striker",
        codename="Striker",
        hp=80,
        max_hp=80,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Quick Strike",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                range=2,
                description="A fast close-range hit for 12 damage.",
            ),
            Ability(
                name="Blitz Rush",
                type="attack",
                damage=18,
                energy_cost=20,
                cooldown=0,
                range=3,
                description="A burst attack that hits for 18 damage at mid range.",
            ),
            Ability(
                name="Evasive Maneuver",
                type="attack",
                damage=0,
                energy_cost=15,
                cooldown=2,
                range=0,
                description="Brace for impact and gain 30% damage reduction for 1 turn.",
                effects=[
                    AbilityEffect(
                        type="status_apply",
                        target="self",
                        status_name="Evasive Maneuver",
                        status_effect_type="damage_reduction",
                        status_value=0.3,
                        status_duration=1,
                    )
                ],
            ),
            Ability(
                name="Execution",
                type="ultimate",
                damage=40,
                energy_cost=80,
                cooldown=8,
                range=2,
                description="A lethal finisher that deals 40 damage.",
            ),
        ],
    )


def _create_guardian() -> Fighter:
    return Fighter(
        id="guardian",
        codename="Guardian",
        hp=120,
        max_hp=120,
        energy=80,
        max_energy=80,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Shield Bash",
                type="attack",
                damage=10,
                energy_cost=0,
                cooldown=0,
                range=2,
                description="A sturdy bash that deals 10 damage.",
            ),
            Ability(
                name="Fortify",
                type="attack",
                damage=0,
                energy_cost=20,
                cooldown=3,
                range=0,
                description="Gain 40% damage reduction for 2 turns.",
                effects=[
                    AbilityEffect(
                        type="status_apply",
                        target="self",
                        status_name="Fortify",
                        status_effect_type="damage_reduction",
                        status_value=0.4,
                        status_duration=2,
                    )
                ],
            ),
            Ability(
                name="Punishing Strike",
                type="attack",
                damage=14,
                energy_cost=25,
                cooldown=0,
                range=2,
                description="Strike for 14 damage and slow the target for 1 turn.",
                effects=[
                    AbilityEffect(
                        type="status_apply",
                        target="opponent",
                        status_name="Punishing Strike",
                        status_effect_type="slow",
                        status_duration=1,
                    )
                ],
            ),
            Ability(
                name="Earthshatter",
                type="ultimate",
                damage=25,
                energy_cost=70,
                cooldown=8,
                range=4,
                description="Smash the arena for 25 damage and stun the target for 1 turn.",
                effects=[
                    AbilityEffect(
                        type="status_apply",
                        target="opponent",
                        status_name="Earthshatter",
                        status_effect_type="stun",
                        status_duration=1,
                    )
                ],
            ),
        ],
    )


def _create_controller() -> Fighter:
    return Fighter(
        id="controller",
        codename="Controller",
        hp=90,
        max_hp=90,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Signal Beam",
                type="attack",
                damage=10,
                energy_cost=0,
                cooldown=0,
                range=5,
                description="A long-range beam that deals 10 damage.",
            ),
            Ability(
                name="Area Denial",
                type="attack",
                damage=12,
                energy_cost=20,
                cooldown=0,
                range=4,
                description="Project force across the arena to deal 12 damage.",
            ),
            Ability(
                name="Repulsor",
                type="attack",
                damage=8,
                energy_cost=25,
                cooldown=2,
                range=3,
                description="Blast the target for 8 damage and push them 2 tiles away.",
                effects=[
                    AbilityEffect(
                        type="knockback",
                        target="opponent",
                        knockback_distance=2,
                    )
                ],
            ),
            Ability(
                name="Overwhelming Force",
                type="ultimate",
                damage=35,
                energy_cost=80,
                cooldown=10,
                range=5,
                description="Unload overwhelming ranged force for 35 damage.",
            ),
        ],
    )


def _create_berserker() -> Fighter:
    return Fighter(
        id="berserker",
        codename="Berserker",
        hp=65,
        max_hp=65,
        energy=120,
        max_energy=120,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Wild Swing",
                type="attack",
                damage=14,
                energy_cost=0,
                cooldown=0,
                range=2,
                description="A brutal swing that deals 14 damage.",
            ),
            Ability(
                name="Bloodlust",
                type="attack",
                damage=0,
                energy_cost=15,
                cooldown=3,
                range=0,
                description="Spend 10 HP to gain 40% bonus damage for 2 turns.",
                effects=[
                    AbilityEffect(
                        type="status_apply",
                        target="self",
                        status_name="Bloodlust",
                        status_effect_type="damage_boost",
                        status_value=0.4,
                        status_duration=2,
                    ),
                    AbilityEffect(
                        type="self_damage",
                        target="self",
                        self_damage=10,
                    ),
                ],
            ),
            Ability(
                name="Reckless Assault",
                type="attack",
                damage=22,
                energy_cost=25,
                cooldown=0,
                range=2,
                description="Crash in for 22 damage and take 8 recoil damage.",
                effects=[
                    AbilityEffect(
                        type="self_damage",
                        target="self",
                        self_damage=8,
                    )
                ],
            ),
            Ability(
                name="Unleashed Fury",
                type="ultimate",
                damage=45,
                energy_cost=80,
                cooldown=8,
                range=2,
                description="An all-in finisher for 45 damage that costs 15 HP.",
                effects=[
                    AbilityEffect(
                        type="self_damage",
                        target="self",
                        self_damage=15,
                    )
                ],
            ),
        ],
    )


_FIGHTER_FACTORY = {
    "striker": _create_striker,
    "guardian": _create_guardian,
    "controller": _create_controller,
    "berserker": _create_berserker,
}


def get_fighter(fighter_id: str) -> Fighter:
    """Get a fresh archetype instance by ID."""
    factory = _FIGHTER_FACTORY.get(fighter_id)
    if factory is None:
        raise ValueError(
            f"Unknown fighter ID: '{fighter_id}'. "
            f"Available fighters: {', '.join(ARCHETYPE_IDS)}"
        )
    return factory()


def get_archetype(fighter_id: str) -> Fighter:
    """Alias for get_fighter during migration."""
    return get_fighter(fighter_id)


def get_all_fighters() -> list[Fighter]:
    """Get fresh instances of all archetypes in the roster."""
    return [get_fighter(fid) for fid in ARCHETYPE_IDS]


def get_all_archetypes() -> list[Fighter]:
    """Alias for get_all_fighters during migration."""
    return get_all_fighters()

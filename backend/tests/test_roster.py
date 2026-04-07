"""Tests for fighter roster definitions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from llm_smash.fighters.roster import (
    ARCHETYPE_IDS,
    ARCHETYPE_PROMPTS,
    BASE_SYSTEM_PROMPT,
    FIGHTER_IDS,
    get_all_archetypes,
    get_fighter,
    get_all_fighters,
    get_archetype,
    get_system_prompt,
)


class TestRoster:
    def test_get_all_fighters_returns_four(self):
        fighters = get_all_fighters()
        assert len(fighters) == 4

    def test_all_fighter_ids_accounted(self):
        fighters = get_all_fighters()
        ids = {f.id for f in fighters}
        assert ids == set(ARCHETYPE_IDS)
        assert FIGHTER_IDS == ARCHETYPE_IDS

    def test_each_fighter_has_required_fields(self):
        for fighter in get_all_fighters():
            assert fighter.id in ARCHETYPE_IDS
            assert fighter.max_hp > 0
            assert fighter.max_energy > 0
            assert fighter.hp == fighter.max_hp, f"{fighter.id} should start at full HP"
            assert fighter.energy == fighter.max_energy, (
                f"{fighter.id} should start at full energy"
            )
            assert len(fighter.abilities) == 4, (
                f"{fighter.id} should have exactly 4 abilities"
            )
            assert fighter.codename, f"{fighter.id} should have a codename"

    def test_each_fighter_has_basic_attack(self):
        """Every fighter should have at least one zero-cost attack."""
        for fighter in get_all_fighters():
            basic_attacks = [
                a for a in fighter.abilities if a.energy_cost == 0 and a.damage > 0
            ]
            assert len(basic_attacks) >= 1, f"{fighter.id} needs a free basic attack"


class TestGetFighter:
    def test_get_striker(self):
        striker = get_fighter("striker")
        assert striker.codename == "Striker"
        assert striker.hp == 80
        assert striker.max_hp == 80

    def test_get_guardian(self):
        guardian = get_fighter("guardian")
        assert guardian.codename == "Guardian"
        assert guardian.hp == 120

    def test_get_controller(self):
        controller = get_fighter("controller")
        assert controller.codename == "Controller"
        assert controller.hp == 90

    def test_get_berserker(self):
        berserker = get_fighter("berserker")
        assert berserker.codename == "Berserker"
        assert berserker.hp == 65
        assert berserker.max_energy == 120

    def test_get_archetype_alias(self):
        guardian = get_archetype("guardian")
        assert guardian.codename == "Guardian"

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown fighter ID"):
            get_fighter("unknown-model")

    def test_get_fighter_returns_fresh_copy(self):
        """Each call should return a new instance, not a shared reference."""
        a = get_fighter("striker")
        b = get_fighter("striker")
        a.hp = 50
        assert b.hp == 80  # Should be unaffected


class TestSystemPrompt:
    def test_system_prompt_includes_base(self):
        prompt = get_system_prompt("striker")
        assert "LLM Smash Bros" in prompt
        assert "JSON" in prompt
        assert BASE_SYSTEM_PROMPT in prompt
        assert '"tactical_summary"' in prompt
        assert "BATTLE MEMORY" in prompt

    def test_system_prompt_includes_archetype_identity(self):
        prompt = get_system_prompt("striker")
        assert "ARCHETYPE: Striker" in prompt
        assert "HP:" in prompt
        assert "Energy:" in prompt
        assert "Range:" in prompt
        assert "TERRAIN TIPS:" in prompt
        prompt_guardian = get_system_prompt("guardian")
        assert "ARCHETYPE: Guardian" in prompt_guardian

    def test_all_archetypes_have_prompts(self):
        for fighter_id in ARCHETYPE_IDS:
            assert fighter_id in ARCHETYPE_PROMPTS, (
                f"Missing archetype prompt for {fighter_id}"
            )

    def test_all_archetypes_have_specific_ability_loadouts(self):
        fighter_names = {
            fighter.id: [ability.name for ability in fighter.abilities]
            for fighter in get_all_archetypes()
        }
        assert fighter_names["striker"] == [
            "Quick Strike",
            "Blitz Rush",
            "Evasive Maneuver",
            "Execution",
        ]
        assert fighter_names["guardian"] == [
            "Shield Bash",
            "Fortify",
            "Punishing Strike",
            "Earthshatter",
        ]
        assert fighter_names["controller"] == [
            "Signal Beam",
            "Area Denial",
            "Repulsor",
            "Overwhelming Force",
        ]
        assert fighter_names["berserker"] == [
            "Wild Swing",
            "Bloodlust",
            "Reckless Assault",
            "Unleashed Fury",
        ]

    def test_unknown_fighter_gets_default_personality(self):
        prompt = get_system_prompt("unknown-model")
        assert "mysterious challenger" in prompt

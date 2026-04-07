"""Tests for fighter roster definitions."""

import pytest
from llm_smash.fighters.roster import (
    get_fighter,
    get_all_fighters,
    get_system_prompt,
    FIGHTER_IDS,
    BASE_SYSTEM_PROMPT,
    PERSONALITY_PROMPTS,
)


class TestRoster:
    def test_get_all_fighters_returns_four(self):
        fighters = get_all_fighters()
        assert len(fighters) == 4

    def test_all_fighter_ids_accounted(self):
        fighters = get_all_fighters()
        ids = {f.id for f in fighters}
        assert ids == set(FIGHTER_IDS)

    def test_each_fighter_has_required_fields(self):
        for fighter in get_all_fighters():
            assert fighter.id in FIGHTER_IDS
            assert fighter.max_hp > 0
            assert fighter.max_energy > 0
            assert fighter.hp == fighter.max_hp, f"{fighter.id} should start at full HP"
            assert fighter.energy == fighter.max_energy, (
                f"{fighter.id} should start at full energy"
            )
            assert len(fighter.abilities) >= 2, (
                f"{fighter.id} should have at least 2 abilities"
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
    def test_get_oracle(self):
        oracle = get_fighter("gpt-4o")
        assert oracle.codename == "The Oracle"
        assert oracle.hp == 100
        assert oracle.max_hp == 100

    def test_get_artisan(self):
        artisan = get_fighter("claude-3.5-sonnet")
        assert artisan.codename == "The Artisan"
        assert artisan.hp == 85

    def test_get_observer(self):
        observer = get_fighter("gemini-1.5-pro")
        assert observer.codename == "The Observer"
        assert observer.hp == 120

    def test_get_swarm(self):
        swarm = get_fighter("llama-3")
        assert swarm.codename == "The Swarm"
        assert swarm.hp == 70
        assert swarm.max_energy == 120

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown fighter ID"):
            get_fighter("unknown-model")

    def test_get_fighter_returns_fresh_copy(self):
        """Each call should return a new instance, not a shared reference."""
        a = get_fighter("gpt-4o")
        b = get_fighter("gpt-4o")
        a.hp = 50
        assert b.hp == 100  # Should be unaffected


class TestSystemPrompt:
    def test_system_prompt_includes_base(self):
        prompt = get_system_prompt("gpt-4o")
        assert "LLM Smash Bros" in prompt
        assert "JSON" in prompt

    def test_system_prompt_includes_personality(self):
        prompt = get_system_prompt("gpt-4o")
        assert "The Oracle" in prompt
        prompt_claude = get_system_prompt("claude-3.5-sonnet")
        assert "The Artisan" in prompt_claude

    def test_all_fighters_have_personality(self):
        for fid in FIGHTER_IDS:
            assert fid in PERSONALITY_PROMPTS, f"Missing personality for {fid}"

    def test_unknown_fighter_gets_default_personality(self):
        prompt = get_system_prompt("unknown-model")
        assert "mysterious challenger" in prompt

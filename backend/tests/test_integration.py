"""Integration tests covering full match lifecycle behavior."""

from __future__ import annotations

import sys
from importlib import import_module
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

state_module = import_module("llm_smash.engine.state")
roster_module = import_module("llm_smash.fighters.roster")
batch_runner_module = import_module("llm_smash.tools.batch_runner")

MatchResult = state_module.MatchResult
TerrainType = state_module.TerrainType
ARCHETYPE_IDS = roster_module.ARCHETYPE_IDS
build_mock_engine = batch_runner_module.build_mock_engine
run_batch = batch_runner_module.run_batch


def _all_matchups() -> list[tuple[str, str]]:
    return [
        *combinations(ARCHETYPE_IDS, 2),
        *((archetype, archetype) for archetype in ARCHETYPE_IDS),
    ]


def _fighter_positions(state_after: dict[str, object]) -> list[tuple[int, int]]:
    fighters = state_after.get("fighters", [])
    assert isinstance(fighters, list)
    positions: list[tuple[int, int]] = []
    for fighter in fighters:
        assert isinstance(fighter, dict)
        position = fighter["position"]
        assert isinstance(position, dict)
        positions.append((int(position["x"]), int(position["y"])))
    return positions


@pytest.mark.asyncio
async def test_full_mock_match_completes():
    """A full mock match runs to completion without errors."""
    engine = build_mock_engine("striker", "guardian", seed=42, max_turns=20)

    result = await engine.run_match()

    assert isinstance(result, MatchResult)
    assert result.match_id
    assert result.total_turns >= 1
    assert result.end_reason in {"ko", "timeout", "draw"}
    assert result.winner in {None, "fighter_a", "fighter_b"}
    assert result.is_draw is (result.winner is None)


@pytest.mark.asyncio
async def test_full_mock_match_produces_valid_turn_logs():
    """Each turn log has valid structure with tactical_summary and trash_talk."""
    engine = build_mock_engine("striker", "controller", seed=7, max_turns=15)

    result = await engine.run_match()

    assert result.turn_log
    for turn in result.turn_log:
        assert turn.turn_number >= 1
        assert set(turn.actions) == {"fighter_a", "fighter_b"}
        assert turn.events
        assert turn.state_after is not None
        for response in turn.actions.values():
            assert response is not None
            assert response.tactical_summary
            assert response.trash_talk is not None


@pytest.mark.asyncio
async def test_full_mock_match_with_terrain():
    """Terrain is generated and appears in the match."""
    engine = build_mock_engine("guardian", "berserker", seed=42, max_turns=20)

    assert engine.state is not None
    assert engine.state.arena.terrain

    result = await engine.run_match()

    touched_non_open_terrain = False
    for turn in result.turn_log:
        assert turn.state_after is not None
        terrain = turn.state_after["arena"]["terrain"]
        assert terrain
        for x, y in _fighter_positions(turn.state_after):
            if (
                TerrainType(terrain.get(f"{x},{y}", TerrainType.OPEN.value))
                != TerrainType.OPEN
            ):
                touched_non_open_terrain = True
                break
        if touched_non_open_terrain:
            break

    assert touched_non_open_terrain


@pytest.mark.asyncio
async def test_all_archetype_matchups_complete():
    """All 6 pairwise matchups + 4 mirrors complete without errors."""
    completed: list[tuple[str, str]] = []

    for archetype_a, archetype_b in _all_matchups():
        engine = build_mock_engine(archetype_a, archetype_b, seed=101, max_turns=20)
        result = await engine.run_match()
        assert result.total_turns >= 1
        completed.append((archetype_a, archetype_b))

    assert len(completed) == 10


@pytest.mark.asyncio
async def test_replay_serialization_roundtrip():
    """Match result serializes to JSON and deserializes back."""
    engine = build_mock_engine("controller", "guardian", seed=17, max_turns=15)

    result = await engine.run_match()
    restored = MatchResult.model_validate_json(result.model_dump_json())

    assert restored.match_id == result.match_id
    assert restored.winner == result.winner
    assert restored.total_turns == result.total_turns
    assert restored.total_fumbles == result.total_fumbles
    assert restored.turn_log[0].actions.keys() == result.turn_log[0].actions.keys()


@pytest.mark.asyncio
async def test_fumble_handling_in_match():
    """A match with high fumble rate still completes."""
    engine = build_mock_engine(
        "striker",
        "guardian",
        seed=29,
        max_turns=10,
        failure_rate=0.9,
    )

    result = await engine.run_match()

    assert result.total_turns >= 1
    assert result.total_fumbles > 0
    for turn in result.turn_log:
        for fighter_id in turn.fumbles:
            response = turn.actions[fighter_id]
            assert response is not None
            assert response.action["type"] == "defend"


@pytest.mark.asyncio
async def test_batch_runner_collects_matchup_statistics():
    """Batch runner returns stable summary statistics for a matchup."""
    result = await run_batch("striker", "guardian", num_matches=5, max_turns=20)

    assert result.matchup == "striker_vs_guardian"
    assert result.total_matches == 5
    assert result.wins_a + result.wins_b + result.draws == 5
    assert 0 <= result.win_rate_a <= 1
    assert 0 <= result.win_rate_b <= 1
    assert result.avg_turns > 0
    assert result.avg_fumbles >= 0

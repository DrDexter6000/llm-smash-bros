"""Batch match runner for integration and balance analysis."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from itertools import combinations
from typing import cast

from llm_smash.engine.game import GameEngine, MatchConfig
from llm_smash.engine.state import Arena, BattleState, MatchPhase, Position
from llm_smash.engine.terrain import TerrainGenerator
from llm_smash.fighters.roster import ARCHETYPE_IDS, get_fighter
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.mock_client import MockLLMClient


@dataclass(slots=True)
class BatchResult:
    matchup: str
    total_matches: int
    wins_a: int
    wins_b: int
    draws: int
    avg_turns: float
    avg_fumbles: float
    win_rate_a: float
    win_rate_b: float


class ArchetypeMatchEngine(GameEngine):
    """Game engine wrapper that supports mirror matches via stable fighter aliases."""

    def __init__(
        self,
        archetypes: tuple[str, str],
        *,
        seed: int | None,
        max_turns: int,
        timeout_per_turn: float,
        failure_rate: float,
        latency_ms: float,
    ):
        config = MatchConfig(
            fighter_ids=["fighter_a", "fighter_b"],
            max_turns=max_turns,
            seed=seed,
            timeout_per_turn=timeout_per_turn,
        )
        self.archetypes = archetypes
        llm_clients = cast(
            dict[str, LLMAdapter],
            {
                "fighter_a": MockLLMClient(
                    fighter_id="fighter_a",
                    seed=seed,
                    failure_rate=failure_rate,
                    latency_ms=latency_ms,
                ),
                "fighter_b": MockLLMClient(
                    fighter_id="fighter_b",
                    seed=None if seed is None else seed + 1,
                    failure_rate=failure_rate,
                    latency_ms=latency_ms,
                ),
            },
        )
        super().__init__(config=config, llm_clients=llm_clients)
        self._ensure_state()

    def _ensure_state(self) -> None:
        if self.state is not None:
            return

        archetype_a, archetype_b = self.archetypes
        fighter_a = get_fighter(archetype_a)
        fighter_b = get_fighter(archetype_b)

        fighter_a.id = "fighter_a"
        fighter_b.id = "fighter_b"
        fighter_a.codename = f"{fighter_a.codename} A"
        fighter_b.codename = f"{fighter_b.codename} B"
        fighter_a.position = Position(x=1, y=3)
        fighter_b.position = Position(x=6, y=3)

        arena = Arena()
        TerrainGenerator(seed=self.config.seed).generate(
            arena,
            start_positions=[fighter_a.position, fighter_b.position],
        )

        self.state = BattleState(
            fighters=[fighter_a, fighter_b],
            arena=arena,
            phase=MatchPhase.READY,
        )


def build_mock_engine(
    archetype_a: str,
    archetype_b: str,
    *,
    seed: int | None,
    max_turns: int = 50,
    timeout_per_turn: float = 8.0,
    failure_rate: float = 0.0,
    latency_ms: float = 0.0,
) -> GameEngine:
    """Create a seeded mock engine for a specific archetype matchup."""
    return ArchetypeMatchEngine(
        (archetype_a, archetype_b),
        seed=seed,
        max_turns=max_turns,
        timeout_per_turn=timeout_per_turn,
        failure_rate=failure_rate,
        latency_ms=latency_ms,
    )


async def run_batch(
    archetype_a: str,
    archetype_b: str,
    num_matches: int = 20,
    max_turns: int = 50,
) -> BatchResult:
    """Run N mock matches and collect summary stats."""
    wins_a = 0
    wins_b = 0
    draws = 0
    total_turns = 0
    total_fumbles = 0

    for seed in range(num_matches):
        engine = build_mock_engine(
            archetype_a,
            archetype_b,
            seed=seed,
            max_turns=max_turns,
        )
        result = await engine.run_match()
        total_turns += result.total_turns
        total_fumbles += result.total_fumbles
        if result.is_draw:
            draws += 1
        elif result.winner == "fighter_a":
            wins_a += 1
        elif result.winner == "fighter_b":
            wins_b += 1

    return BatchResult(
        matchup=f"{archetype_a}_vs_{archetype_b}",
        total_matches=num_matches,
        wins_a=wins_a,
        wins_b=wins_b,
        draws=draws,
        avg_turns=total_turns / num_matches,
        avg_fumbles=total_fumbles / num_matches,
        win_rate_a=wins_a / num_matches,
        win_rate_b=wins_b / num_matches,
    )


def all_matchups() -> list[tuple[str, str]]:
    """Return all cross-archetype and mirror matchups."""
    return [
        *combinations(ARCHETYPE_IDS, 2),
        *((archetype, archetype) for archetype in ARCHETYPE_IDS),
    ]


async def run_all_matchups(
    *,
    num_matches: int = 20,
    max_turns: int = 50,
) -> list[BatchResult]:
    """Run the full 10-matchup balance matrix."""
    results: list[BatchResult] = []
    for archetype_a, archetype_b in all_matchups():
        results.append(
            await run_batch(
                archetype_a,
                archetype_b,
                num_matches=num_matches,
                max_turns=max_turns,
            )
        )
    return results


def format_results_table(results: list[BatchResult]) -> str:
    """Render batch results as a markdown table."""
    lines = [
        "| Matchup | A Wins | B Wins | Draws | A Win% | Avg Turns | Avg Fumbles |",
        "|---------|--------|--------|-------|--------|-----------|-------------|",
    ]
    for result in results:
        matchup = result.matchup.replace("_vs_", " vs ").replace("_", " ").title()
        lines.append(
            "| "
            f"{matchup} | {result.wins_a} | {result.wins_b} | {result.draws} | "
            f"{result.win_rate_a * 100:.1f}% | {result.avg_turns:.1f} | {result.avg_fumbles:.1f} |"
        )
    return "\n".join(lines)


async def _main() -> None:
    results = await run_all_matchups()
    print(format_results_table(results))


if __name__ == "__main__":
    asyncio.run(_main())

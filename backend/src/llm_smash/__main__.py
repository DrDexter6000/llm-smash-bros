"""Entry point for ``python -m llm_smash``."""

from __future__ import annotations

import argparse
import asyncio

from llm_smash.cli import run_cli_match
from llm_smash.fighters.roster import FIGHTER_IDS


def main() -> None:
    """Parse CLI args and run a match."""
    parser = argparse.ArgumentParser(description="LLM Smash Bros — AI Fighting Game")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Use mock LLM clients (default when --live is not set)",
    )
    mode_group.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Use real LLM APIs (configure FIGHTER1_*/FIGHTER2_* in .env)",
    )
    parser.add_argument(
        "--fighters",
        nargs=2,
        default=["gpt-4o", "claude-3.5-sonnet"],
        choices=FIGHTER_IDS,
        metavar="FIGHTER",
        help=(
            "Two fighter IDs to pit against each other. Available: "
            f"{', '.join(FIGHTER_IDS)}"
        ),
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum turns (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic matches",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Seconds per turn before a fumble (default: 8 for mock, 30 for live)",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        default=False,
        help="Skip API connection check before live matches",
    )
    args = parser.parse_args()

    # Default to mock when neither flag is specified
    use_mock = not args.live

    # Pick a sensible timeout: explicit flag > mode-based default
    timeout: float = (
        args.timeout if args.timeout is not None else (8.0 if use_mock else 30.0)
    )

    asyncio.run(
        run_cli_match(
            fighter_ids=args.fighters,
            use_mock=use_mock,
            max_turns=args.max_turns,
            seed=args.seed,
            timeout=timeout,
            skip_preflight=args.no_preflight,
        )
    )


if __name__ == "__main__":
    main()

"""Tests for recent-turn summaries used in battle memory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm_smash.engine.state import ActionResponse, TurnEvent, TurnLog
from llm_smash.engine.turn_summary import summarize_turn


def test_summarize_turn_attack_defend_damage():
    turn_log = TurnLog(
        turn_number=4,
        actions={
            "striker": ActionResponse(
                turn=4,
                action={
                    "type": "attack",
                    "ability": "Blitz Rush",
                    "target": "guardian",
                },
                tactical_summary="Bursting through cover.",
            ),
            "guardian": ActionResponse(
                turn=4,
                action={"type": "defend"},
                tactical_summary="Weathering the hit.",
            ),
        },
        events=[
            TurnEvent(
                type="damage",
                source_id="striker",
                target_id="guardian",
                value=18,
                description="Guardian takes 18 damage.",
            )
        ],
    )

    assert summarize_turn(turn_log, "striker") == {
        "turn": 4,
        "you": "attacked with Blitz Rush → 18 dmg",
        "opponent": "defended",
    }


def test_summarize_turn_wait_and_hazard_event():
    turn_log = TurnLog(
        turn_number=5,
        actions={
            "controller": ActionResponse(
                turn=5,
                action={"type": "wait"},
                tactical_summary="Recharging for a ranged spike.",
            ),
            "guardian": ActionResponse(
                turn=5,
                action={
                    "type": "attack",
                    "ability": "Shield Bash",
                    "target": "controller",
                },
                tactical_summary="Closing the distance.",
            ),
        },
        events=[
            TurnEvent(
                type="damage",
                source_id="guardian",
                target_id="controller",
                value=10,
                description="Controller takes 10 damage.",
            ),
            TurnEvent(
                type="hazard",
                source_id="arena",
                description="A firewall appears at (3, 1).",
            ),
        ],
    )

    assert summarize_turn(turn_log, "controller") == {
        "turn": 5,
        "you": "waited (+5 energy)",
        "opponent": "used Shield Bash → 10 dmg to you",
        "notable": "A firewall appears at (3, 1).",
    }


def test_summarize_turn_fumble_and_ko_notable():
    turn_log = TurnLog(
        turn_number=6,
        actions={
            "berserker": ActionResponse(
                turn=6,
                action={"type": "defend"},
                tactical_summary="Fallback engaged.",
            ),
            "guardian": ActionResponse(
                turn=6,
                action={
                    "type": "attack",
                    "ability": "Earthshatter",
                    "target": "berserker",
                },
                tactical_summary="Ending this.",
            ),
        },
        events=[
            TurnEvent(
                type="fumble",
                source_id="berserker",
                description="berserker fumbled and defaults to defend.",
            ),
            TurnEvent(
                type="damage",
                source_id="guardian",
                target_id="berserker",
                value=25,
                description="Berserker takes 25 damage.",
            ),
            TurnEvent(
                type="ko",
                target_id="berserker",
                description="Berserker is knocked out!",
            ),
        ],
        fumbles=["berserker"],
    )

    assert summarize_turn(turn_log, "berserker") == {
        "turn": 6,
        "you": "fumbled",
        "opponent": "used Earthshatter → 25 dmg to you",
        "notable": "Berserker is knocked out!",
    }

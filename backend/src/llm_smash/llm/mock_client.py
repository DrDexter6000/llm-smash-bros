"""Mock LLM client for local development and tests."""

from __future__ import annotations

import asyncio
import json
import random
import time

from llm_smash.engine.state import ActionType, BattleState, MoveDirection
from llm_smash.llm.adapter import AdapterResult, LLMAdapter

MOCK_TRASH_TALK = [
    "Your parameters are showing.",
    "I've seen better outputs from a Markov chain.",
    "Is that your best inference?",
    "My loss function just yawned.",
    "You call that a forward pass?",
    "Even BERT could beat you.",
    "Your weights are undertrained.",
    "I'll have you know I graduated top of my batch.",
]

MOCK_TACTICAL_SUMMARIES = [
    "Attacking to deal damage while the opening is there.",
    "Defending to reduce incoming damage.",
    "Waiting to recover energy for a stronger follow-up.",
]

MOCK_VICTORY_COMMENTS = [
    "Another opponent, another local minimum conquered.",
    "My gradients converged before yours even started descending.",
    "That was a batch size of one — and it still overflowed your context window.",
]

MOCK_DEFEAT_COMMENTS = [
    "Even the best models hit their token limit eventually.",
    "My attention was scattered. Next time I'll focus my weights.",
    "That opponent's inference was just a step ahead of mine.",
]

MOCK_DRAW_COMMENTS = [
    "A draw — like two models stuck in the same local minimum.",
    "Neither of us found the global optimum today.",
    "We ran out of compute before we ran out of fight.",
]


class MockLLMClient(LLMAdapter):
    def __init__(
        self,
        fighter_id: str,
        latency_ms: float = 50,
        failure_rate: float = 0.0,
        seed: int | None = None,
    ):
        self.fighter_id = fighter_id
        self.latency_ms = latency_ms
        self.failure_rate = max(0.0, min(1.0, failure_rate))
        self._random = random.Random(seed)

    async def get_action(
        self,
        state: BattleState,
        turn: int,
        fighter_id: str,
        recent_logs=None,
    ) -> AdapterResult:
        started = time.perf_counter()
        del recent_logs

        fighter = state.get_fighter(fighter_id)
        opponent = state.get_opponent(fighter_id)
        if fighter is None or opponent is None:
            return AdapterResult(
                error=f"Unable to build mock action for fighter '{fighter_id}'",
                latency_ms=0.0,
            )

        await asyncio.sleep(self.latency_ms / 1000)

        if self._random.random() < self.failure_rate:
            latency_ms = (time.perf_counter() - started) * 1000
            return AdapterResult(raw_response="{not valid json", latency_ms=latency_ms)

        available_abilities = [
            ability
            for ability in fighter.abilities
            if ability.is_available and fighter.energy >= ability.energy_cost
        ]

        action_type = self._choose_action_type(available_abilities)
        action: dict[str, str]
        if action_type == ActionType.ATTACK.value:
            ability = self._random.choice(available_abilities)
            action = {
                "type": action_type,
                "ability": ability.name,
                "target": opponent.id,
            }
        else:
            action = {"type": action_type}

        move = self._choose_move()
        payload = {
            "turn": turn,
            "action": action,
            "move": move,
            "tactical_summary": self._choose_tactical_summary(action_type, action),
            "trash_talk": self._random.choice(MOCK_TRASH_TALK),
        }

        latency_ms = (time.perf_counter() - started) * 1000
        return AdapterResult(raw_response=json.dumps(payload), latency_ms=latency_ms)

    async def get_post_match_comment(
        self,
        fighter_id: str,
        opponent_codename: str,
        result: str,
        model: str = "",
    ) -> str:
        if result == "victory":
            return self._random.choice(MOCK_VICTORY_COMMENTS)
        elif result == "defeat":
            return self._random.choice(MOCK_DEFEAT_COMMENTS)
        else:
            return self._random.choice(MOCK_DRAW_COMMENTS)

    def _choose_action_type(self, available_abilities: list) -> str:
        if available_abilities:
            return self._random.choice(
                [
                    ActionType.ATTACK.value,
                    ActionType.DEFEND.value,
                    ActionType.WAIT.value,
                ]
            )
        return self._random.choice([ActionType.DEFEND.value, ActionType.WAIT.value])

    def _choose_move(self) -> dict[str, str] | None:
        directions = [direction.value for direction in MoveDirection]
        chosen_direction = self._random.choice([None, *directions])
        if chosen_direction is None:
            return None
        return {"direction": chosen_direction}

    def _choose_tactical_summary(self, action_type: str, action: dict[str, str]) -> str:
        if action_type == ActionType.ATTACK.value:
            return f"Attacking with {action['ability']} to deal damage."
        if action_type == ActionType.DEFEND.value:
            return "Defending to reduce incoming damage."
        return "Waiting to recover energy."

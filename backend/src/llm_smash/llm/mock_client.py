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

MOCK_MONOLOGUES = [
    "Calculating optimal strategy...",
    "Opponent appears vulnerable.",
    "Energy levels sufficient for assault.",
    "Defensive posture may be wise here.",
    "Time to press the advantage.",
    "Analyzing opponent's movement pattern.",
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
        self, state: BattleState, turn: int, fighter_id: str
    ) -> AdapterResult:
        started = time.perf_counter()

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
            "inner_monologue": self._random.choice(MOCK_MONOLOGUES),
            "trash_talk": self._random.choice(MOCK_TRASH_TALK),
        }

        latency_ms = (time.perf_counter() - started) * 1000
        return AdapterResult(raw_response=json.dumps(payload), latency_ms=latency_ms)

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

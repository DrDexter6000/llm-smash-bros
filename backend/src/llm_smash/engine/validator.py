"""Validation of raw LLM turn responses."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

from llm_smash.engine.state import ActionResponse, ActionType, BattleState


class ValidationResult(BaseModel):
    is_valid: bool
    response: ActionResponse | None = None
    error: str | None = None


class ResponseValidator:
    """Validate raw JSON action responses from LLMs."""

    _CODE_BLOCK_PATTERN = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
    _THINK_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)

    def validate(
        self, raw: str, turn: int, fighter_id: str, state: BattleState
    ) -> ValidationResult:
        """Validate a raw JSON string from an LLM response."""
        cleaned = self._strip_think_tags(raw)
        cleaned = self._strip_markdown_code_blocks(cleaned)
        if not cleaned:
            return ValidationResult(is_valid=False, error="Empty response")

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return ValidationResult(is_valid=False, error=f"Invalid JSON: {exc.msg}")

        try:
            response = ActionResponse.model_validate(payload)
        except ValidationError as exc:
            return ValidationResult(is_valid=False, error=f"Invalid schema: {exc}")

        if response.turn != turn:
            return ValidationResult(
                is_valid=False,
                error=f"Turn mismatch: expected {turn}, got {response.turn}",
            )

        fighter = state.get_fighter(fighter_id)
        if fighter is None:
            return ValidationResult(
                is_valid=False, error=f"Unknown fighter: {fighter_id}"
            )

        action_type = response.action.get("type")
        valid_action_types = {action.value for action in ActionType}
        if action_type not in valid_action_types:
            return ValidationResult(
                is_valid=False, error=f"Invalid action type: {action_type}"
            )

        if action_type == ActionType.ATTACK.value:
            ability_name = response.action.get("ability")
            if not ability_name:
                return ValidationResult(
                    is_valid=False, error="Attack action missing ability"
                )

            target = response.action.get("target")
            if not target:
                return ValidationResult(
                    is_valid=False, error="Attack action missing target"
                )

            ability = fighter.get_ability(ability_name)
            if ability is None:
                return ValidationResult(
                    is_valid=False, error=f"Unknown ability: {ability_name}"
                )

            if not ability.is_available:
                return ValidationResult(
                    is_valid=False,
                    error=f"Ability '{ability.name}' is on cooldown",
                )

            if fighter.energy < ability.energy_cost:
                return ValidationResult(
                    is_valid=False,
                    error=(
                        f"Not enough energy for '{ability.name}': "
                        f"need {ability.energy_cost}, have {fighter.energy}"
                    ),
                )

        return ValidationResult(is_valid=True, response=response)

    def _strip_markdown_code_blocks(self, raw: str) -> str:
        stripped = raw.strip()
        if not stripped:
            return ""

        match = self._CODE_BLOCK_PATTERN.match(stripped)
        if match:
            return match.group(1).strip()

        return stripped

    def _strip_think_tags(self, raw: str) -> str:
        """Remove <think>...</think> reasoning blocks emitted by some models."""
        return self._THINK_TAG_PATTERN.sub("", raw).strip()

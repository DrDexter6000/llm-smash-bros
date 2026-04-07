"""Core game engine turn loop and match lifecycle."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field, model_validator

from llm_smash.engine.combat import CombatResolver
from llm_smash.engine.state import (
    ActionResponse,
    ActionType,
    Arena,
    BattleState,
    Fighter,
    MatchPhase,
    MatchResult,
    Position,
    StatusEffect,
    TurnEvent,
    TurnLog,
)
from llm_smash.engine.validator import ResponseValidator
from llm_smash.fighters.roster import get_fighter
from llm_smash.llm.adapter import AdapterResult, LLMAdapter


class MatchConfig(BaseModel):
    """Configuration for a two-fighter match."""

    fighter_ids: list[str]
    max_turns: int = 50
    timeout_per_turn: float = 8.0
    seed: int | None = None

    @model_validator(mode="after")
    def validate_match(self) -> "MatchConfig":
        if len(self.fighter_ids) != 2:
            raise ValueError("MatchConfig requires exactly 2 fighter IDs")
        if len(set(self.fighter_ids)) != 2:
            raise ValueError("MatchConfig fighter IDs must be unique")
        if self.max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        if self.timeout_per_turn <= 0:
            raise ValueError("timeout_per_turn must be greater than 0")
        return self


class GameEngine:
    """Runs a complete LLM Smash Bros match."""

    def __init__(
        self,
        config: MatchConfig,
        llm_clients: dict[str, LLMAdapter],
        event_callback: Callable[[TurnLog], Awaitable[None]] | None = None,
    ):
        self.config = config
        self.llm_clients = llm_clients
        self.event_callback = event_callback
        self.combat = CombatResolver(seed=config.seed)
        self.validator = ResponseValidator()
        self.state: BattleState | None = None

        missing_clients = [
            fighter_id
            for fighter_id in self.config.fighter_ids
            if fighter_id not in self.llm_clients
        ]
        if missing_clients:
            raise ValueError(
                f"Missing LLM clients for fighters: {', '.join(missing_clients)}"
            )

    async def run_match(self) -> MatchResult:
        """Run a complete match from initialization to resolution."""
        self._ensure_state()
        assert self.state is not None
        self.state.phase = MatchPhase.FIGHTING

        turn_log: list[TurnLog] = []
        total_fumbles = 0
        result: MatchResult | None = None

        for turn_num in range(1, self.config.max_turns + 1):
            turn = await self._execute_turn(turn_num)
            turn_log.append(turn)
            total_fumbles += len(turn.fumbles)

            result = self._check_end_conditions()
            if self.event_callback is not None:
                await self.event_callback(turn)
            if result is not None:
                break

        if result is None:
            raise RuntimeError("Match ended without a result")

        self.state.phase = MatchPhase.RESOLVED
        result.turn_log = turn_log
        result.total_turns = len(turn_log)
        result.total_fumbles = total_fumbles
        return result

    async def _execute_turn(self, turn_num: int) -> TurnLog:
        """Execute a single turn of movement, combat, and environmental effects."""
        self._ensure_state()
        assert self.state is not None
        self.state.turn = turn_num

        fighter_ids = list(self.config.fighter_ids)
        fighters = {fighter.id: fighter for fighter in self.state.fighters}
        events: list[TurnEvent] = []
        actions: dict[str, ActionResponse | None] = {}
        fumbles: list[str] = []
        status_effects_to_tick = {
            fighter.id: {id(effect) for effect in fighter.status_effects}
            for fighter in self.state.fighters
        }

        request_fighter_ids: list[str] = []
        for fighter_id in fighter_ids:
            fighter = fighters[fighter_id]
            if fighter.has_status("stun"):
                actions[fighter_id] = self._build_status_action(
                    fighter_id=fighter_id,
                    action_type=ActionType.DEFEND.value,
                    inner_monologue="Stunned. Forced into a defensive stance.",
                    trash_talk="...ngh...",
                )
                events.append(
                    TurnEvent(
                        type="stun",
                        source_id=fighter_id,
                        description=f"{fighter.codename} is stunned and cannot act!",
                    )
                )
                continue
            request_fighter_ids.append(fighter_id)

        adapter_results = await asyncio.gather(
            *(
                self._request_action(fighter_id, turn_num)
                for fighter_id in request_fighter_ids
            )
        )
        adapter_map = dict(zip(request_fighter_ids, adapter_results, strict=True))

        for fighter_id in request_fighter_ids:
            adapter_result = adapter_map[fighter_id]
            validated_response: ActionResponse
            if (
                adapter_result.timed_out
                or adapter_result.error is not None
                or adapter_result.raw_response is None
            ):
                validated_response = self._handle_fumble(fighter_id)
                fumbles.append(fighter_id)
                events.append(
                    TurnEvent(
                        type="fumble",
                        source_id=fighter_id,
                        value=0,
                        description=f"{fighter_id} fumbled and defaults to defend.",
                    )
                )
            else:
                validation = self.validator.validate(
                    adapter_result.raw_response,
                    turn=turn_num,
                    fighter_id=fighter_id,
                    state=self.state,
                )
                if not validation.is_valid or validation.response is None:
                    validated_response = self._handle_fumble(fighter_id)
                    fumbles.append(fighter_id)
                    events.append(
                        TurnEvent(
                            type="fumble",
                            source_id=fighter_id,
                            value=0,
                            description=(
                                f"{fighter_id} produced an invalid action and fumbled."
                            ),
                        )
                    )
                else:
                    validated_response = validation.response

            actions[fighter_id] = validated_response

        for fighter_id in fighter_ids:
            fighter = fighters[fighter_id]
            response = actions[fighter_id]
            if response is None:
                continue
            if fighter.has_status("slow"):
                if response.move:
                    events.append(
                        TurnEvent(
                            type="slow",
                            source_id=fighter_id,
                            description=(
                                f"{fighter.codename} is slowed and cannot move this turn."
                            ),
                        )
                    )
                response.move = None
            new_position = self.combat.resolve_movement(
                fighter,
                response.move["direction"] if response.move else None,
                self.state.arena.width,
                self.state.arena.height,
            )
            if new_position != fighter.position:
                fighter.position = new_position
                events.append(
                    TurnEvent(
                        type="move",
                        source_id=fighter_id,
                        description=(
                            f"{fighter.codename} moves to ({new_position.x}, {new_position.y})."
                        ),
                    )
                )

        defending = {
            fighter_id
            for fighter_id, response in actions.items()
            if response is not None
            and response.action.get("type") == ActionType.DEFEND.value
        }

        pending_damage: dict[str, int] = {fighter_id: 0 for fighter_id in fighter_ids}
        pending_effects: list[tuple[str, str, str]] = []
        alive_at_action_start = {
            fighter_id: fighters[fighter_id].is_alive for fighter_id in fighter_ids
        }

        for fighter_id in fighter_ids:
            fighter = fighters[fighter_id]
            opponent = self.state.get_opponent(fighter_id)
            response = actions[fighter_id]
            if (
                opponent is None
                or response is None
                or not alive_at_action_start[fighter_id]
            ):
                continue

            action_type = response.action.get("type")
            fighter.last_action = {
                "action": response.action,
                "move": response.move,
                "inner_monologue": response.inner_monologue,
                "trash_talk": response.trash_talk,
            }

            if action_type == ActionType.ATTACK.value:
                ability_name = response.action.get("ability", "")
                ability = fighter.get_ability(ability_name)
                if ability is None:
                    continue
                fighter.energy = max(0, fighter.energy - ability.energy_cost)
                damage = self.combat.calculate_damage(
                    fighter,
                    opponent,
                    ability,
                    is_defending=opponent.id in defending,
                )
                pending_damage[opponent.id] += damage
                pending_effects.append((fighter_id, opponent.id, ability.name))
                if ability.cooldown > 0:
                    ability.cooldown_remaining = ability.cooldown
                events.append(
                    TurnEvent(
                        type="ability_used",
                        source_id=fighter_id,
                        target_id=opponent.id,
                        value=damage,
                        description=(
                            f"{fighter.codename} uses {ability.name} on {opponent.codename}."
                        ),
                    )
                )
            elif action_type == ActionType.DEFEND.value:
                events.append(
                    TurnEvent(
                        type="defend",
                        source_id=fighter_id,
                        description=f"{fighter.codename} braces for impact.",
                    )
                )
            elif action_type == ActionType.WAIT.value:
                self.combat.apply_wait_bonus(fighter)
                events.append(
                    TurnEvent(
                        type="wait",
                        source_id=fighter_id,
                        value=5,
                        description=f"{fighter.codename} waits and regains focus.",
                    )
                )

        ability_by_name = {
            (fighter.id, ability.name): ability
            for fighter in self.state.fighters
            for ability in fighter.abilities
        }

        for fighter_id, damage in pending_damage.items():
            if damage <= 0:
                continue
            target = fighters[fighter_id]
            target.hp = max(0, target.hp - damage)
            attacker_id = next(
                (
                    source_id
                    for source_id, response in actions.items()
                    if response is not None
                    and response.action.get("type") == ActionType.ATTACK.value
                    and response.action.get("target") == fighter_id
                ),
                "",
            )
            events.append(
                TurnEvent(
                    type="damage",
                    source_id=attacker_id,
                    target_id=fighter_id,
                    value=damage,
                    description=f"{target.codename} takes {damage} damage.",
                )
            )

        for source_id, target_id, ability_name in pending_effects:
            source = fighters[source_id]
            target = fighters[target_id]
            ability = ability_by_name[(source_id, ability_name)]
            events.extend(self._apply_ability_effects(source, target, ability))

        for fighter_id in fighter_ids:
            fighter = fighters[fighter_id]
            self.combat.apply_ability_cooldowns(fighter)
            self.combat.apply_energy_regen(fighter)
            events.extend(self.combat.apply_hazard_damage(fighter, self.state.arena))
            self.combat.tick_status_effects(
                fighter,
                active_effect_ids=status_effects_to_tick[fighter_id],
            )

        self.combat.tick_hazards(self.state.arena)

        if self.combat.should_spawn_hazard(turn_num):
            hazard = self.combat.spawn_hazard(
                self.state.arena,
                occupied_positions=[
                    fighter.position for fighter in self.state.fighters
                ],
            )
            if hazard is not None:
                events.append(
                    TurnEvent(
                        type="hazard",
                        source_id="arena",
                        value=hazard.damage,
                        description=(
                            f"A {hazard.type} appears at "
                            f"({hazard.position.x}, {hazard.position.y})."
                        ),
                    )
                )

        for fighter in self.state.fighters:
            if fighter.hp == 0:
                events.append(
                    TurnEvent(
                        type="ko",
                        target_id=fighter.id,
                        description=f"{fighter.codename} is knocked out!",
                    )
                )

        return TurnLog(
            turn_number=turn_num,
            actions=actions,
            events=events,
            state_after=self.state.model_dump(mode="json"),
            fumbles=fumbles,
        )

    def _check_end_conditions(self) -> MatchResult | None:
        """Return a final result if the match has ended, else None."""
        assert self.state is not None
        fighter_a, fighter_b = self.state.fighters

        if fighter_a.hp <= 0 and fighter_b.hp <= 0:
            return MatchResult(
                match_id=self.state.match_id,
                winner=None,
                is_draw=True,
                end_reason="draw",
            )

        if fighter_a.hp <= 0:
            return MatchResult(
                match_id=self.state.match_id,
                winner=fighter_b.id,
                is_draw=False,
                end_reason="ko",
            )

        if fighter_b.hp <= 0:
            return MatchResult(
                match_id=self.state.match_id,
                winner=fighter_a.id,
                is_draw=False,
                end_reason="ko",
            )

        if self.state.turn >= self.config.max_turns:
            hp_a = fighter_a.hp_percentage
            hp_b = fighter_b.hp_percentage
            if hp_a == hp_b:
                return MatchResult(
                    match_id=self.state.match_id,
                    winner=None,
                    is_draw=True,
                    end_reason="timeout",
                )
            winner = fighter_a.id if hp_a > hp_b else fighter_b.id
            return MatchResult(
                match_id=self.state.match_id,
                winner=winner,
                is_draw=False,
                end_reason="timeout",
            )

        return None

    def _handle_fumble(self, fighter_id: str) -> ActionResponse:
        """Fallback action when the LLM times out or responds invalidly."""
        assert self.state is not None
        fighter = self.state.get_fighter(fighter_id)
        if fighter is None:
            raise ValueError(f"Unknown fighter for fumble handling: {fighter_id}")

        penalty = max(1, fighter.max_hp // 10)
        fighter.hp = max(0, fighter.hp - penalty)
        return ActionResponse(
            turn=self.state.turn,
            action={"type": ActionType.DEFEND.value},
            move=None,
            inner_monologue="Signal lost. Defensive fallback engaged.",
            trash_talk="...buffer underrun...",
        )

    def _build_status_action(
        self,
        fighter_id: str,
        action_type: str,
        inner_monologue: str,
        trash_talk: str,
    ) -> ActionResponse:
        assert self.state is not None
        return ActionResponse(
            turn=self.state.turn,
            action={"type": action_type},
            move=None,
            inner_monologue=inner_monologue,
            trash_talk=trash_talk,
        )

    def _apply_ability_effects(
        self, source: Fighter, target: Fighter, ability
    ) -> list[TurnEvent]:
        events: list[TurnEvent] = []
        for effect in ability.effects:
            effect_target = source if effect.target == "self" else target
            if effect.type == "status_apply":
                if effect_target is target and not target.is_alive:
                    continue
                status = StatusEffect(
                    name=effect.status_name or effect.status_effect_type,
                    turns_remaining=effect.status_duration,
                    effect_type=effect.status_effect_type,
                    value=effect.status_value,
                )
                self.combat.apply_status_effect(effect_target, status)
                events.append(
                    TurnEvent(
                        type="status_applied",
                        source_id=source.id,
                        target_id=effect_target.id,
                        description=(
                            f"{effect_target.codename} gains {status.effect_type} "
                            f"for {status.turns_remaining} turn(s)."
                        ),
                    )
                )
            elif effect.type == "self_damage" and effect.self_damage > 0:
                source.hp = max(0, source.hp - effect.self_damage)
                events.append(
                    TurnEvent(
                        type="self_damage",
                        source_id=source.id,
                        target_id=source.id,
                        value=effect.self_damage,
                        description=(
                            f"{source.codename} takes {effect.self_damage} self-damage."
                        ),
                    )
                )
            elif (
                effect.type == "knockback"
                and effect.knockback_distance > 0
                and target.is_alive
            ):
                new_position = self._resolve_knockback(
                    source=source,
                    target=target,
                    distance=effect.knockback_distance,
                )
                if new_position != target.position:
                    target.position = new_position
                    events.append(
                        TurnEvent(
                            type="knockback",
                            source_id=source.id,
                            target_id=target.id,
                            description=(
                                f"{target.codename} is knocked back to "
                                f"({new_position.x}, {new_position.y})."
                            ),
                        )
                    )
        return events

    def _resolve_knockback(
        self, source: Fighter, target: Fighter, distance: int
    ) -> Position:
        assert self.state is not None
        dx = (
            0
            if target.position.x == source.position.x
            else (1 if target.position.x > source.position.x else -1)
        )
        dy = (
            0
            if target.position.y == source.position.y
            else (1 if target.position.y > source.position.y else -1)
        )
        new_x = target.position.x
        new_y = target.position.y
        for _ in range(distance):
            candidate = Position(
                x=max(0, min(self.state.arena.width - 1, new_x + dx)),
                y=max(0, min(self.state.arena.height - 1, new_y + dy)),
            )
            if candidate == Position(x=new_x, y=new_y):
                break
            new_x, new_y = candidate.x, candidate.y
        return Position(x=new_x, y=new_y)

    def _ensure_state(self) -> None:
        if self.state is not None:
            return

        fighters = [get_fighter(fighter_id) for fighter_id in self.config.fighter_ids]
        fighters[0].position = Position(x=1, y=3)
        fighters[1].position = Position(x=6, y=3)

        self.state = BattleState(
            fighters=fighters,
            arena=Arena(),
            phase=MatchPhase.READY,
        )

    async def _request_action(self, fighter_id: str, turn_num: int) -> AdapterResult:
        assert self.state is not None
        client = self.llm_clients[fighter_id]
        try:
            return await asyncio.wait_for(
                client.get_action(self.state, turn_num, fighter_id),
                timeout=self.config.timeout_per_turn,
            )
        except asyncio.TimeoutError:
            return AdapterResult(timed_out=True, error="timeout")
        except Exception as exc:  # pragma: no cover - defensive path
            return AdapterResult(error=str(exc))

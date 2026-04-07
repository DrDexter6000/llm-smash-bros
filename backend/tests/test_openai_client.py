"""Tests for the OpenAI LLM adapter client."""

from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

state_module = import_module("llm_smash.engine.state")
adapter_module = import_module("llm_smash.llm.adapter")
roster_module = import_module("llm_smash.fighters.roster")
openai_client_module = import_module("llm_smash.llm.openai_client")
openai = import_module("openai")

Ability = state_module.Ability
Arena = state_module.Arena
BattleState = state_module.BattleState
Fighter = state_module.Fighter
LLMAdapter = adapter_module.LLMAdapter
MatchPhase = state_module.MatchPhase
OpenAIClient = openai_client_module.OpenAIClient
Position = state_module.Position
get_system_prompt = roster_module.get_system_prompt


def make_completion(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def make_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def get_create_kwargs(create: AsyncMock) -> dict[str, Any]:
    assert create.await_args is not None
    return cast(dict[str, Any], create.await_args.kwargs)


@pytest.fixture
def sample_state() -> BattleState:
    f1 = Fighter(
        id="gpt-4o",
        codename="The Oracle",
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Logic Missile",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=4,
            )
        ],
    )
    f2 = Fighter(
        id="claude-3.5-sonnet",
        codename="The Artisan",
        hp=85,
        max_hp=85,
        energy=100,
        max_energy=100,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Code Slice",
                type="attack",
                damage=14,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            )
        ],
    )
    arena = Arena(width=8, height=6)
    return BattleState(
        match_id="test",
        turn=3,
        phase=MatchPhase.FIGHTING,
        fighters=[f1, f2],
        arena=arena,
    )


class TestOpenAIClient:
    def test_openai_client_implements_adapter(self):
        client = OpenAIClient()

        assert isinstance(client, LLMAdapter)

    @pytest.mark.asyncio
    async def test_sends_system_prompt_and_battle_state(
        self, sample_state: BattleState
    ):
        create = AsyncMock(return_value=make_completion('{"action":"wait"}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            await client.get_action(sample_state, turn=7, fighter_id="gpt-4o")

        kwargs = get_create_kwargs(create)
        assert kwargs["messages"] == [
            {"role": "system", "content": get_system_prompt("gpt-4o")},
            {
                "role": "user",
                "content": json.dumps(sample_state.to_fighter_perspective("gpt-4o")),
            },
        ]

    @pytest.mark.asyncio
    async def test_uses_json_mode(self, sample_state: BattleState):
        create = AsyncMock(return_value=make_completion('{"action":"wait"}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            await client.get_action(sample_state, turn=5, fighter_id="gpt-4o")

        assert get_create_kwargs(create)["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_returns_raw_content_string(self, sample_state: BattleState):
        create = AsyncMock(return_value=make_completion('{"trash_talk":"hi"}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            result = await client.get_action(sample_state, turn=2, fighter_id="gpt-4o")

        assert result.raw_response == '{"trash_talk":"hi"}'
        assert result.error is None
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_measures_latency(self, sample_state: BattleState):
        create = AsyncMock(return_value=make_completion('{"move":null}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            result = await client.get_action(sample_state, turn=1, fighter_id="gpt-4o")

        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_api_error_returns_error_result(self, sample_state: BattleState):
        create = AsyncMock(
            side_effect=openai.APIError(
                message="boom", request=make_request(), body=None
            )
        )
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            result = await client.get_action(sample_state, turn=4, fighter_id="gpt-4o")

        assert result.raw_response is None
        assert result.error == "boom"
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_api_timeout_returns_timed_out(self, sample_state: BattleState):
        create = AsyncMock(side_effect=openai.APITimeoutError(request=make_request()))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            result = await client.get_action(sample_state, turn=4, fighter_id="gpt-4o")

        assert result.raw_response is None
        assert result.error == "Request timed out."
        assert result.timed_out is True

    @pytest.mark.asyncio
    async def test_connection_error_returns_error_result(
        self, sample_state: BattleState
    ):
        create = AsyncMock(
            side_effect=openai.APIConnectionError(request=make_request())
        )
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            result = await client.get_action(sample_state, turn=4, fighter_id="gpt-4o")

        assert result.raw_response is None
        assert result.error == "Connection error."
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_default_model_is_gpt_4o(self, sample_state: BattleState):
        create = AsyncMock(return_value=make_completion('{"turn":3}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient()
            await client.get_action(sample_state, turn=3, fighter_id="gpt-4o")

        assert get_create_kwargs(create)["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_custom_model_passed_to_api(self, sample_state: BattleState):
        create = AsyncMock(return_value=make_completion('{"turn":3}'))
        async_openai = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch(
            "llm_smash.llm.openai_client.openai.AsyncOpenAI", return_value=async_openai
        ):
            client = OpenAIClient(model="gpt-4.1-mini")
            await client.get_action(sample_state, turn=3, fighter_id="gpt-4o")

        assert get_create_kwargs(create)["model"] == "gpt-4.1-mini"

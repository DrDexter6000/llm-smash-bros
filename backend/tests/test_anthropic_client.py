"""Tests for the Anthropic LLM adapter client."""

from __future__ import annotations

import json
from importlib import import_module
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

state_module = import_module("llm_smash.engine.state")
adapter_module = import_module("llm_smash.llm.adapter")
anthropic_client_module = import_module("llm_smash.llm.anthropic_client")
roster_module = import_module("llm_smash.fighters.roster")
anthropic = import_module("anthropic")

Ability = state_module.Ability
Arena = state_module.Arena
BattleState = state_module.BattleState
Fighter = state_module.Fighter
MatchPhase = state_module.MatchPhase
Position = state_module.Position
AdapterResult = adapter_module.AdapterResult
LLMAdapter = adapter_module.LLMAdapter
AnthropicClient = anthropic_client_module.AnthropicClient
JSON_ONLY_SUFFIX = anthropic_client_module.JSON_ONLY_SUFFIX
DEFAULT_MODEL = anthropic_client_module.DEFAULT_MODEL
get_system_prompt = roster_module.get_system_prompt


@pytest.fixture
def sample_state() -> BattleState:
    f1 = Fighter(
        id="striker",
        codename="Striker",
        hp=80,
        max_hp=80,
        energy=100,
        max_energy=100,
        position=Position(x=1, y=3),
        abilities=[
            Ability(
                name="Quick Strike",
                type="attack",
                damage=12,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            )
        ],
    )
    f2 = Fighter(
        id="guardian",
        codename="Guardian",
        hp=120,
        max_hp=120,
        energy=80,
        max_energy=80,
        position=Position(x=6, y=3),
        abilities=[
            Ability(
                name="Shield Bash",
                type="attack",
                damage=10,
                energy_cost=0,
                cooldown=0,
                cooldown_remaining=0,
                range=2,
            )
        ],
    )
    return BattleState(
        match_id="test",
        turn=3,
        phase=MatchPhase.FIGHTING,
        fighters=[f1, f2],
        arena=Arena(width=8, height=6),
    )


def _make_response(text: str):
    text_block = type("TextBlock", (), {"text": text})()
    return type("Message", (), {"content": [text_block]})()


def _request() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.fixture
def mock_messages_create() -> Generator[AsyncMock, None, None]:
    with patch("llm_smash.llm.anthropic_client.AsyncAnthropic") as mock_client_cls:
        create = AsyncMock(return_value=_make_response('{"turn": 3}'))
        mock_client_cls.return_value.messages.create = create
        yield create


def _await_kwargs(mock_messages_create: AsyncMock) -> dict[str, Any]:
    await_args = mock_messages_create.await_args
    assert await_args is not None
    return dict(await_args.kwargs)


class TestAnthropicClient:
    def test_anthropic_client_implements_adapter(self):
        client = AnthropicClient()

        assert isinstance(client, LLMAdapter)

    @pytest.mark.asyncio
    async def test_sends_system_prompt_separately(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        client = AnthropicClient()

        await client.get_action(sample_state, turn=7, fighter_id="striker")

        kwargs = _await_kwargs(mock_messages_create)
        assert kwargs["system"] == get_system_prompt("striker")
        assert kwargs["messages"] == [
            {"role": "user", "content": kwargs["messages"][0]["content"]}
        ]
        assert get_system_prompt("striker") not in kwargs["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_sends_battle_state_as_user_message(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        client = AnthropicClient()

        await client.get_action(sample_state, turn=7, fighter_id="striker")

        user_content = _await_kwargs(mock_messages_create)["messages"][0]["content"]
        expected_json = json.dumps(sample_state.to_fighter_perspective("striker"))
        assert expected_json in user_content

    @pytest.mark.asyncio
    async def test_appends_json_emphasis_to_user_message(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        client = AnthropicClient()

        await client.get_action(sample_state, turn=7, fighter_id="striker")

        user_content = _await_kwargs(mock_messages_create)["messages"][0]["content"]
        assert user_content.endswith(JSON_ONLY_SUFFIX)

    @pytest.mark.asyncio
    async def test_returns_raw_content_string(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        raw_text = '{"turn": 99, "action": {"type": "wait"}}'
        mock_messages_create.return_value = _make_response(raw_text)
        client = AnthropicClient()

        result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result == AdapterResult(
            raw_response=raw_text,
            latency_ms=result.latency_ms,
        )

    @pytest.mark.asyncio
    async def test_measures_latency(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        client = AnthropicClient()

        result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_api_error_returns_error_result(self, sample_state: BattleState):
        error = anthropic.APIError("boom", _request(), body=None)
        with patch("llm_smash.llm.anthropic_client.AsyncAnthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create = AsyncMock(side_effect=error)
            client = AnthropicClient()

            result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result.raw_response is None
        assert result.error == str(error)
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_api_timeout_returns_timed_out(self, sample_state: BattleState):
        error = anthropic.APITimeoutError(request=_request())
        with patch("llm_smash.llm.anthropic_client.AsyncAnthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create = AsyncMock(side_effect=error)
            client = AnthropicClient()

            result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result.raw_response is None
        assert result.error == str(error)
        assert result.timed_out is True

    @pytest.mark.asyncio
    async def test_connection_error_returns_error_result(
        self, sample_state: BattleState
    ):
        error = anthropic.APIConnectionError(request=_request())
        with patch("llm_smash.llm.anthropic_client.AsyncAnthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create = AsyncMock(side_effect=error)
            client = AnthropicClient()

            result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result.raw_response is None
        assert result.error == str(error)
        assert result.timed_out is False

    def test_default_model_is_claude_sonnet(self):
        client = AnthropicClient()

        assert client.model == DEFAULT_MODEL

    @pytest.mark.asyncio
    async def test_max_tokens_set(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        client = AnthropicClient()

        await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert _await_kwargs(mock_messages_create)["max_tokens"] == 1024

    @pytest.mark.asyncio
    async def test_extracts_text_from_content_blocks(
        self, sample_state: BattleState, mock_messages_create: AsyncMock
    ):
        mock_messages_create.return_value = _make_response(
            '{"source": "content-block"}'
        )
        client = AnthropicClient()

        result = await client.get_action(sample_state, turn=7, fighter_id="striker")

        assert result.raw_response == '{"source": "content-block"}'

"""Tests for retry logic in live LLM clients."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

anthropic_client_module = import_module("llm_smash.llm.anthropic_client")
openai_client_module = import_module("llm_smash.llm.openai_client")
anthropic = import_module("anthropic")
openai = import_module("openai")

AnthropicClient = anthropic_client_module.AnthropicClient
OpenAIClient = openai_client_module.OpenAIClient


def _make_openai_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def _make_anthropic_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _make_status_response(request: httpx.Request, status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=request)


def _openai_status_error(status_code: int) -> Exception:
    request = _make_openai_request()
    return openai.APIStatusError(
        f"status {status_code}",
        response=_make_status_response(request, status_code),
        body=None,
    )


def _anthropic_status_error(status_code: int) -> Exception:
    request = _make_anthropic_request()
    return anthropic.APIStatusError(
        f"status {status_code}",
        response=_make_status_response(request, status_code),
        body=None,
    )


def _make_openai_client() -> OpenAIClient:
    return OpenAIClient()


def _make_anthropic_client() -> AnthropicClient:
    with patch("llm_smash.llm.anthropic_client.AsyncAnthropic"):
        return AnthropicClient()


CLIENT_CASES: list[tuple[str, Any, Any, Any]] = [
    (
        "openai",
        openai_client_module,
        _make_openai_client,
        _openai_status_error,
    ),
    (
        "anthropic",
        anthropic_client_module,
        _make_anthropic_client,
        _anthropic_status_error,
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("_provider", "module_under_test", "client_factory", "status_error_factory"),
    CLIENT_CASES,
)
async def test_retry_api_call_returns_first_success_without_retry(
    _provider: str,
    module_under_test: Any,
    client_factory: Any,
    status_error_factory: Any,
):
    del status_error_factory
    client = client_factory()
    api_call = AsyncMock(return_value="ok")

    with (
        patch.object(module_under_test.random, "uniform", return_value=0.0),
        patch.object(module_under_test.asyncio, "sleep", new=AsyncMock()) as sleep_mock,
    ):
        result = await client._retry_api_call(api_call)

    assert result == "ok"
    assert api_call.await_count == 1
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("_provider", "module_under_test", "client_factory", "status_error_factory"),
    CLIENT_CASES,
)
async def test_retry_api_call_retries_transient_error_then_succeeds(
    _provider: str,
    module_under_test: Any,
    client_factory: Any,
    status_error_factory: Any,
):
    client = client_factory()
    transient_error = status_error_factory(429)
    api_call = AsyncMock(side_effect=[transient_error, "ok"])

    with (
        patch.object(module_under_test.random, "uniform", return_value=0.0),
        patch.object(module_under_test.asyncio, "sleep", new=AsyncMock()) as sleep_mock,
    ):
        result = await client._retry_api_call(api_call)

    assert result == "ok"
    assert api_call.await_count == 2
    sleep_mock.assert_awaited_once_with(client.BASE_DELAY)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("_provider", "module_under_test", "client_factory", "status_error_factory"),
    CLIENT_CASES,
)
async def test_retry_api_call_raises_non_transient_error_immediately(
    _provider: str,
    module_under_test: Any,
    client_factory: Any,
    status_error_factory: Any,
):
    client = client_factory()
    non_transient_error = status_error_factory(400)
    api_call = AsyncMock(side_effect=non_transient_error)

    with (
        patch.object(module_under_test.random, "uniform", return_value=0.0),
        patch.object(module_under_test.asyncio, "sleep", new=AsyncMock()) as sleep_mock,
    ):
        with pytest.raises(type(non_transient_error)) as exc_info:
            await client._retry_api_call(api_call)

    assert exc_info.value is non_transient_error
    assert api_call.await_count == 1
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("_provider", "module_under_test", "client_factory", "status_error_factory"),
    CLIENT_CASES,
)
async def test_retry_api_call_raises_last_error_after_retries_exhausted(
    _provider: str,
    module_under_test: Any,
    client_factory: Any,
    status_error_factory: Any,
):
    client = client_factory()
    transient_error = status_error_factory(503)
    api_call = AsyncMock(side_effect=transient_error)

    with (
        patch.object(module_under_test.random, "uniform", return_value=0.0),
        patch.object(module_under_test.asyncio, "sleep", new=AsyncMock()) as sleep_mock,
    ):
        with pytest.raises(type(transient_error)) as exc_info:
            await client._retry_api_call(api_call)

    assert exc_info.value is transient_error
    assert api_call.await_count == client.MAX_RETRIES + 1
    assert sleep_mock.await_args_list == [
        ((client.BASE_DELAY,), {}),
        ((client.BASE_DELAY * 2,), {}),
        ((client.BASE_DELAY * 4,), {}),
    ]

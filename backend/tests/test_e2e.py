"""End-to-end tests for the full REST + WebSocket match lifecycle."""

from __future__ import annotations

import asyncio
import sys
from contextlib import ExitStack
from importlib import import_module
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

app_module = import_module("llm_smash.api.app")
state_module = import_module("llm_smash.engine.state")

create_app = cast(Any, app_module.create_app)
MatchResult = cast(Any, state_module.MatchResult)

ARCHETYPE_IDS = ["striker", "guardian", "controller", "berserker"]


@pytest.fixture
def app():
    app = create_app()
    app.state.match_manager._mock_client_latency_ms = 80.0
    return app


@pytest.fixture
def ws_client(app):
    with TestClient(app) as client:
        yield client


def _portal_call(ws_client: TestClient, func: Any, *args: Any) -> Any:
    assert ws_client.portal is not None
    return ws_client.portal.call(func, *args)


async def _post_json(app, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(path, json=payload)
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


async def _get_json(
    app, path: str
) -> tuple[int, dict[str, Any] | list[dict[str, Any]]]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    return response.status_code, cast(
        dict[str, Any] | list[dict[str, Any]], response.json()
    )


async def _wait_for_match_completion(app, match_id: str) -> dict[str, Any]:
    last_payload: dict[str, Any] | None = None

    for _ in range(200):
        status_code, payload = await _get_json(app, f"/api/matches/{match_id}")
        assert status_code == 200
        assert isinstance(payload, dict)
        last_payload = payload

        if payload["status"] == "completed":
            return payload
        if payload["status"] == "error":
            pytest.fail(f"match entered error state: {payload}")

        await asyncio.sleep(0.05)

    pytest.fail(f"match did not complete in time: {last_payload}")


def _create_match(ws_client: TestClient, app, **overrides: Any) -> str:
    payload = {
        "fighter1_archetype": "striker",
        "fighter2_archetype": "guardian",
        "max_turns": 12,
        "seed": 42,
    }
    payload.update(overrides)

    response = _portal_call(ws_client, _post_json, app, "/api/matches", payload)
    return cast(str, response["match_id"])


def _get(
    ws_client: TestClient, app, path: str
) -> dict[str, Any] | list[dict[str, Any]]:
    status_code, payload = _portal_call(ws_client, _get_json, app, path)
    assert status_code == 200
    return payload


def _wait_for_completion(ws_client: TestClient, app, match_id: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        _portal_call(ws_client, _wait_for_match_completion, app, match_id),
    )


def _collect_stream_messages(
    websocket,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    first_message = websocket.receive_json()
    assert first_message["type"] == "match_start"

    turns: list[dict[str, Any]] = []
    while True:
        message = websocket.receive_json()
        if message["type"] == "turn":
            turns.append(cast(dict[str, Any], message["turn_log"]))
            continue

        assert message["type"] == "match_end"
        return first_message, turns, cast(dict[str, Any], message["result"])


def test_full_match_lifecycle(ws_client: TestClient, app) -> None:
    match_id = _create_match(ws_client, app, max_turns=10, seed=101)

    with ws_client.websocket_connect(f"/api/matches/{match_id}/ws") as websocket:
        start_message, streamed_turns, end_result = _collect_stream_messages(websocket)

    assert start_message["match_id"] == match_id
    assert len(start_message["fighters"]) == 2
    assert "arena" in start_message
    assert streamed_turns

    detail = cast(dict[str, Any], _get(ws_client, app, f"/api/matches/{match_id}"))
    replay = cast(
        dict[str, Any], _get(ws_client, app, f"/api/matches/{match_id}/replay")
    )

    assert detail["status"] == "completed"
    assert detail["winner"] == end_result["winner"]
    assert detail["turn_count"] == end_result["total_turns"] == len(streamed_turns)

    replay_result = MatchResult.model_validate(replay)
    assert replay_result.match_id == match_id
    assert replay["turn_log"] == streamed_turns


def test_concurrent_matches_complete_without_interference(
    ws_client: TestClient, app
) -> None:
    match_ids = [
        _create_match(
            ws_client,
            app,
            fighter1_archetype=fighter1,
            fighter2_archetype=fighter2,
            max_turns=12,
            seed=seed,
        )
        for seed, (fighter1, fighter2) in enumerate(
            [
                ("striker", "guardian"),
                ("controller", "berserker"),
                ("guardian", "controller"),
            ],
            start=201,
        )
    ]

    with ExitStack() as stack:
        websockets = {
            match_id: stack.enter_context(
                ws_client.websocket_connect(f"/api/matches/{match_id}/ws")
            )
            for match_id in match_ids
        }

        results = {
            match_id: _collect_stream_messages(websocket)
            for match_id, websocket in websockets.items()
        }

    for match_id, (start_message, streamed_turns, end_result) in results.items():
        assert start_message["match_id"] == match_id
        assert streamed_turns
        assert end_result["match_id"] == match_id

        detail = _wait_for_completion(ws_client, app, match_id)
        assert detail["status"] == "completed"
        assert detail["match_id"] == match_id
        assert detail["winner"] == end_result["winner"]
        assert detail["turn_count"] == len(streamed_turns)


def test_all_unique_archetype_matchups_complete(ws_client: TestClient, app) -> None:
    for seed, (fighter1, fighter2) in enumerate(
        combinations(ARCHETYPE_IDS, 2), start=301
    ):
        match_id = _create_match(
            ws_client,
            app,
            fighter1_archetype=fighter1,
            fighter2_archetype=fighter2,
            max_turns=12,
            seed=seed,
        )

        detail = _wait_for_completion(ws_client, app, match_id)

        assert detail["status"] == "completed"
        assert detail["match_id"] == match_id
        assert detail["turn_count"] > 0
        assert [fighter["archetype_id"] for fighter in detail["fighters"]] == [
            fighter1,
            fighter2,
        ]


def test_replay_matches_live_streamed_turns(ws_client: TestClient, app) -> None:
    match_id = _create_match(
        ws_client,
        app,
        fighter1_archetype="controller",
        fighter2_archetype="berserker",
        max_turns=12,
        seed=401,
    )

    with ws_client.websocket_connect(f"/api/matches/{match_id}/ws") as websocket:
        _, streamed_turns, end_result = _collect_stream_messages(websocket)

    replay = cast(
        dict[str, Any], _get(ws_client, app, f"/api/matches/{match_id}/replay")
    )

    assert replay["match_id"] == match_id
    assert replay["winner"] == end_result["winner"]
    assert replay["total_turns"] == len(streamed_turns)
    assert replay["turn_log"] == streamed_turns

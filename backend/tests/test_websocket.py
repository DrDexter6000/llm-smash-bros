"""Tests for WebSocket match streaming."""

from __future__ import annotations

import sys
import time
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from starlette.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

app_module = import_module("llm_smash.api.app")

create_app = cast(Any, app_module.create_app)


def _create_match(client: TestClient, **overrides: object) -> str:
    payload = {
        "fighter1_archetype": "striker",
        "fighter2_archetype": "guardian",
        "max_turns": 10,
        "seed": 42,
    }
    payload.update(overrides)

    response = client.post("/api/matches", json=payload)

    assert response.status_code == 201
    return response.json()["match_id"]


def _wait_for_turns(client: TestClient, match_id: str, minimum_turns: int = 1) -> None:
    deadline = time.time() + 5
    while time.time() < deadline:
        response = client.get(f"/api/matches/{match_id}/turns")
        assert response.status_code == 200
        if len(response.json()["turns"]) >= minimum_turns:
            return
        time.sleep(0.05)
    raise AssertionError("match did not produce turns in time")


def test_websocket_full_match_stream() -> None:
    app = create_app()
    app.state.match_manager._mock_client_latency_ms = 150.0
    with TestClient(app) as client:
        match_id = _create_match(client)

        with client.websocket_connect(f"/api/matches/{match_id}/ws") as websocket:
            first_message = websocket.receive_json()
            assert first_message["type"] == "match_start"
            assert first_message["match_id"] == match_id
            assert len(first_message["fighters"]) == 2
            assert "arena" in first_message

            turn_numbers: list[int] = []
            while True:
                message = websocket.receive_json()
                if message["type"] == "turn":
                    turn_numbers.append(message["turn_number"])
                    assert message["turn_log"]["turn_number"] == message["turn_number"]
                    continue

                assert message["type"] == "match_end"
                assert turn_numbers
                assert message["result"]["match_id"] == match_id
                break


def test_websocket_match_not_found() -> None:
    with TestClient(create_app()) as client:
        with client.websocket_connect("/api/matches/nonexistent/ws") as websocket:
            message = websocket.receive_json()
            assert message == {"type": "error", "message": "Match not found"}


def test_websocket_ping_pong() -> None:
    app = create_app()
    app.state.match_manager._mock_client_latency_ms = 150.0
    with TestClient(app) as client:
        match_id = _create_match(client, max_turns=8)

        with client.websocket_connect(f"/api/matches/{match_id}/ws") as websocket:
            first_message = websocket.receive_json()
            assert first_message["type"] == "match_start"

            websocket.send_json({"type": "ping"})
            assert websocket.receive_json() == {"type": "pong"}


def test_websocket_late_join_receives_state_sync() -> None:
    app = create_app()
    app.state.match_manager._mock_client_latency_ms = 100.0
    with TestClient(app) as client:
        match_id = _create_match(client, max_turns=20)
        _wait_for_turns(client, match_id, minimum_turns=1)

        with client.websocket_connect(f"/api/matches/{match_id}/ws") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "state_sync"
            assert message["turns_so_far"]
            assert message["current_state"]["match_id"] == match_id
            assert (
                message["current_state"]["turn"]
                >= message["turns_so_far"][-1]["turn_number"]
            )

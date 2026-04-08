"""Tests for the FastAPI match API."""

from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

main_module = import_module("llm_smash.__main__")
app_module = import_module("llm_smash.api.app")
cli_module = import_module("llm_smash.cli")
state_module = import_module("llm_smash.engine.state")

main = cast(Any, main_module.main)
create_app = cast(Any, app_module.create_app)
serialize_match_result = cast(Any, cli_module.serialize_match_result)
MatchResult = cast(Any, state_module.MatchResult)


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _create_match(client: AsyncClient, **overrides: object) -> str:
    payload = {
        "fighter1_archetype": "striker",
        "fighter2_archetype": "guardian",
        "max_turns": 10,
        "seed": 42,
    }
    payload.update(overrides)

    response = await client.post("/api/matches", json=payload)

    assert response.status_code == 201
    return response.json()["match_id"]


async def _wait_for_completion(client: AsyncClient, match_id: str) -> dict[str, object]:
    last_payload: dict[str, object] | None = None

    for _ in range(80):
        response = await client.get(f"/api/matches/{match_id}")
        assert response.status_code == 200
        last_payload = cast(dict[str, object], response.json())
        status = cast(str, last_payload["status"])
        if status == "completed":
            return last_payload
        if status == "error":
            pytest.fail(f"match entered error state: {last_payload}")
        await asyncio.sleep(0.05)

    pytest.fail(f"match did not complete in time: {last_payload}")


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_and_get_match_full_lifecycle(client: AsyncClient):
    match_id = await _create_match(client)

    detail = await _wait_for_completion(client, match_id)

    assert detail["match_id"] == match_id
    assert detail["status"] == "completed"
    assert cast(int, detail["turn_count"]) > 0
    assert len(cast(list[object], detail["fighters"])) == 2
    assert detail["winner"] in {"fighter_a", "fighter_b", None}

    turns_response = await client.get(f"/api/matches/{match_id}/turns")
    assert turns_response.status_code == 200
    turns_payload = cast(dict[str, object], turns_response.json())
    assert turns_payload["match_id"] == match_id
    assert len(cast(list[object], turns_payload["turns"])) == cast(
        int, detail["turn_count"]
    )


@pytest.mark.asyncio
async def test_list_matches_returns_recent_matches(client: AsyncClient):
    first_match_id = await _create_match(client, seed=1)
    second_match_id = await _create_match(client, seed=2)

    await _wait_for_completion(client, first_match_id)
    await _wait_for_completion(client, second_match_id)

    response = await client.get("/api/matches", params={"limit": 2})

    assert response.status_code == 200
    payload = cast(list[dict[str, object]], response.json())
    assert len(payload) == 2
    assert {item["match_id"] for item in payload} == {first_match_id, second_match_id}


@pytest.mark.asyncio
async def test_get_replay_matches_cli_serialization_format(client: AsyncClient):
    match_id = await _create_match(client)
    detail = await _wait_for_completion(client, match_id)

    response = await client.get(f"/api/matches/{match_id}/replay")

    assert response.status_code == 200
    replay_payload = cast(dict[str, object], response.json())
    replay_result = MatchResult.model_validate(replay_payload)

    assert replay_payload == serialize_match_result(replay_result)
    assert replay_payload["match_id"] == match_id
    assert replay_payload["total_turns"] == cast(int, detail["turn_count"])


@pytest.mark.asyncio
async def test_list_archetypes(client: AsyncClient):
    response = await client.get("/api/archetypes")

    assert response.status_code == 200
    payload = cast(list[dict[str, Any]], response.json())
    assert {item["id"] for item in payload} == {
        "striker",
        "guardian",
        "controller",
        "berserker",
    }
    assert all(item["abilities"] for item in payload)


@pytest.mark.asyncio
async def test_get_match_returns_404_for_unknown_match(client: AsyncClient):
    response = await client.get("/api/matches/nonexistent")

    assert response.status_code == 404
    assert response.json()["detail"] == "Match not found"


def test_main_serve_flag_starts_uvicorn(monkeypatch):
    calls: dict[str, object] = {}

    def fake_run(app, host: str, port: int) -> None:
        calls["app"] = app
        calls["host"] = host
        calls["port"] = port

    monkeypatch.setattr("uvicorn.run", fake_run)
    monkeypatch.setattr(sys, "argv", ["llm_smash", "--serve", "--port", "9001"])

    main()

    assert calls["host"] == "0.0.0.0"
    assert calls["port"] == 9001
    app = calls["app"]
    assert app is not None
    assert getattr(app, "title") == "LLM Smash Bros API"

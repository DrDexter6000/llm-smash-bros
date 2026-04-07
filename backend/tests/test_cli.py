"""Tests for the CLI match runner."""

from __future__ import annotations

import io
import sys
from importlib import import_module
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

cli_module = import_module("llm_smash.cli")
state_module = import_module("llm_smash.engine.state")

run_cli_match = cli_module.run_cli_match
MatchResult = state_module.MatchResult


class TestCLI:
    @pytest.mark.asyncio
    async def test_cli_match_completes(self, capsys):
        """A mock match runs and prints turn output."""
        result = await run_cli_match(
            fighter_ids=["striker", "guardian"],
            use_mock=True,
            max_turns=10,
            seed=42,
        )

        captured = capsys.readouterr()

        assert "TURN 1" in captured.out
        assert result is not None
        assert result.total_turns > 0

    @pytest.mark.asyncio
    async def test_cli_outputs_winner_or_draw(self, capsys):
        """Match output includes winner or draw announcement."""
        result = await run_cli_match(
            fighter_ids=["striker", "guardian"],
            use_mock=True,
            max_turns=10,
            seed=42,
        )

        captured = capsys.readouterr()

        assert result is not None
        assert "WINNER" in captured.out.upper() or "DRAW" in captured.out.upper()

    @pytest.mark.asyncio
    async def test_cli_match_returns_match_result(self):
        """Function returns a MatchResult object."""
        result = await run_cli_match(
            fighter_ids=["striker", "guardian"],
            use_mock=True,
            max_turns=5,
            seed=42,
        )

        assert isinstance(result, MatchResult)

    @pytest.mark.asyncio
    async def test_cli_match_handles_gbk_stdout(self, monkeypatch):
        """CLI output should not crash on Windows GBK terminals."""
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="gbk", errors="replace")
        monkeypatch.setattr(sys, "stdout", stream)

        result = await run_cli_match(
            fighter_ids=["striker", "guardian"],
            use_mock=True,
            max_turns=5,
            seed=42,
        )

        stream.flush()
        output = raw.getvalue().decode("gbk", errors="replace")

        assert result.total_turns > 0
        assert "MATCH COMPLETE" in output

    @pytest.mark.asyncio
    async def test_cli_mirror_match_completes(self):
        """Mirror matches should run to completion in the CLI path."""
        result = await run_cli_match(
            fighter_ids=["berserker", "berserker"],
            use_mock=True,
            max_turns=5,
            seed=42,
        )

        assert isinstance(result, MatchResult)
        assert result.total_turns > 0

    @pytest.mark.asyncio
    async def test_cli_mirror_match_shows_distinct_fighter_labels(self, capsys):
        """Mirror matches should render distinguishable fighter labels."""
        await run_cli_match(
            fighter_ids=["berserker", "berserker"],
            use_mock=True,
            max_turns=5,
            seed=42,
        )

        captured = capsys.readouterr()

        assert "BERSERKER A" in captured.out.upper()
        assert "BERSERKER B" in captured.out.upper()

    def test_build_live_clients_preserves_slot_keys_for_mirror_matches(
        self, monkeypatch
    ):
        """Live clients should remain keyed by unique fighter slots."""
        monkeypatch.setenv("FIGHTER1_PROVIDER", "openai")
        monkeypatch.setenv("FIGHTER1_API_KEY", "key-1")
        monkeypatch.setenv("FIGHTER1_MODEL", "model-1")
        monkeypatch.setenv("FIGHTER2_PROVIDER", "anthropic")
        monkeypatch.setenv("FIGHTER2_API_KEY", "key-2")
        monkeypatch.setenv("FIGHTER2_MODEL", "model-2")

        class FakeOpenAIClient:
            def __init__(self, *, model, api_key, base_url):
                self.model = model
                self.api_key = api_key
                self.base_url = base_url

        class FakeAnthropicClient:
            def __init__(self, *, model, api_key, base_url):
                self.model = model
                self.api_key = api_key
                self.base_url = base_url

        monkeypatch.setattr(cli_module, "OpenAIClient", FakeOpenAIClient)
        monkeypatch.setattr(cli_module, "AnthropicClient", FakeAnthropicClient)

        clients = cli_module._build_live_clients(["fighter_a", "fighter_b"])

        assert set(clients) == {"fighter_a", "fighter_b"}
        assert clients["fighter_a"].model == "model-1"
        assert clients["fighter_b"].model == "model-2"

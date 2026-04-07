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

        assert "Turn 1" in captured.out
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
        stream = io.TextIOWrapper(raw, encoding="gbk", errors="strict")
        monkeypatch.setattr(sys, "stdout", stream)

        result = await run_cli_match(
            fighter_ids=["striker", "guardian"],
            use_mock=True,
            max_turns=5,
            seed=42,
        )

        stream.flush()
        output = raw.getvalue().decode("gbk")

        assert result.total_turns > 0
        assert "MATCH COMPLETE" in output

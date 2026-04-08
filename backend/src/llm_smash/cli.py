"""CLI runner for LLM Smash Bros mock and real matches."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from llm_smash.engine.game import GameEngine, MatchConfig
from llm_smash.engine.state import (
    ActionType,
    Arena,
    BattleState,
    Fighter,
    MatchPhase,
    MatchResult,
    Position,
    TurnEvent,
    TurnLog,
)
from llm_smash.engine.terrain import TerrainGenerator
from llm_smash.fighters.roster import get_archetype, get_fighter
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.anthropic_client import AnthropicClient
from llm_smash.llm.mock_client import MockLLMClient
from llm_smash.llm.openai_client import OpenAIClient

_stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
if callable(_stdout_reconfigure):
    try:
        _stdout_reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def get_hp_color(hp: int, max_hp: int) -> str:
    """Return a color for the HP bar based on the current ratio."""
    ratio = hp / max_hp if max_hp > 0 else 0
    if ratio > 0.5:
        return "green"
    elif ratio > 0.25:
        return "yellow"
    return "red"


def display_fighter_panel(
    fighter: Fighter, turn_log: TurnLog | None = None, model_label: str = ""
) -> Panel:
    """Render a rich Panel for a single fighter's status and last action."""
    action_text = "None"
    tactical_summary = ""
    trash_talk = ""
    fumbled = False
    fumble_reason = ""

    if turn_log:
        if fighter.id in turn_log.fumbles:
            fumbled = True
            fumble_reason = "Cognitive breakdown"
        else:
            resp = turn_log.actions.get(fighter.id)
            if resp:
                action_type = resp.action.get("type", "?")
                if action_type == ActionType.ATTACK.value:
                    ability = resp.action.get("ability", "?")
                    action_text = f"[magenta]⚔️ Attack ({ability})[/magenta]"
                elif action_type == ActionType.DEFEND.value:
                    action_text = f"[blue]🛡️ Defend[/blue]"
                elif action_type == ActionType.WAIT.value:
                    action_text = f"[dim]💤 Wait[/dim]"

                tactical_summary = resp.tactical_summary or ""
                trash_talk = resp.trash_talk or ""

    hp_color = get_hp_color(fighter.hp, fighter.max_hp)

    content = Table.grid(padding=0)
    content.add_column()

    hp_bar_len = 20
    hp_ratio = fighter.hp / fighter.max_hp if fighter.max_hp > 0 else 0
    hp_filled = int(hp_bar_len * hp_ratio)
    hp_empty = hp_bar_len - hp_filled
    hp_bar_str = f"[{hp_color}]{'█' * hp_filled}{'░' * hp_empty}[/{hp_color}]"

    content.add_row(
        f"HP: {hp_bar_str} {fighter.hp}/{fighter.max_hp}  Energy: [cyan]{fighter.energy}/{fighter.max_energy}[/cyan]"
    )

    status_str = "none"
    if fighter.status_effects:
        status_str = ", ".join(
            f"{eff.effect_type}({eff.turns_remaining}t)"
            for eff in fighter.status_effects
        )

    content.add_row(
        f"Pos: ({fighter.position.x},{fighter.position.y})  Status: {status_str}"
    )

    if fumbled:
        content.add_row(f"\n[red bold]💥 FUMBLE![/red bold]")
        content.add_row(f'[dim]"{fumble_reason}"[/dim]')
    else:
        content.add_row(f"Action: {action_text}")
        if tactical_summary:
            content.add_row(f'Strategy: [dim italic]"{tactical_summary}"[/dim italic]')
        if trash_talk:
            content.add_row(f'Trash: [white]"{trash_talk}"[/white]')

    panel_title = fighter.codename.upper()
    if model_label:
        panel_title += f" ({model_label})"

    return Panel(
        content,
        title=f"[{hp_color} bold]{panel_title}[/]",
        title_align="left",
        border_style=hp_color,
    )


def display_turn(
    engine: GameEngine,
    turn_log: TurnLog,
    fighters: dict[str, Fighter],
    model_labels: dict[str, str] | None = None,
) -> None:
    """Print the full turn display including arena and fighters."""
    assert engine.state is not None
    model_labels = model_labels or {}

    # Build legend with model names
    if len(engine.state.fighters) >= 2:
        f0, f1 = engine.state.fighters[0], engine.state.fighters[1]
        a_label = f"{f0.codename}"
        b_label = f"{f1.codename}"
        if f0.id in model_labels:
            a_label += f" ({model_labels[f0.id]})"
        if f1.id in model_labels:
            b_label += f" ({model_labels[f1.id]})"
        legend = f"A={a_label}  B={b_label}"
    else:
        legend = ""

    perspective_id = engine.state.fighters[0].id if engine.state.fighters else ""
    arena_grid = engine.state.arena.to_ascii_grid(
        engine.state.fighters,
        perspective_fighter_id=perspective_id,
        legend_override=legend,
    )

    grid_panel = Panel(
        Text(arena_grid, style="white", justify="left"),
        title="Arena",
        title_align="left",
        border_style="white",
    )

    events_text = []
    for event in turn_log.events:
        if event.type == "damage":
            events_text.append(f"[red]💥 {event.description}[/red]")
        elif event.type == "ko":
            events_text.append(f"[red bold]☠️  {event.description}[/red bold]")
        elif event.type == "hazard" and event.source_id == "arena":
            events_text.append(f"[yellow]⚠️  {event.description}[/yellow]")

    events_panel = None
    if events_text:
        events_panel = Panel(
            "\n".join(events_text),
            border_style="yellow",
            title="Events",
            title_align="left",
        )

    fighter_panels = []
    for f in engine.state.fighters:
        fighter_panels.append(
            display_fighter_panel(f, turn_log, model_label=model_labels.get(f.id, ""))
        )

    console.rule(f"[bold white]TURN {turn_log.turn_number}[/bold white]")
    console.print(grid_panel)
    for p in fighter_panels:
        console.print(p)
    if events_panel:
        console.print(events_panel)
    console.print("")


def display_match_result(
    result: MatchResult,
    fighters_map: dict[str, Fighter],
    model_labels: dict[str, str] | None = None,
) -> None:
    """Print the final match outcome statistics."""
    console.rule("[bold white]MATCH COMPLETE[/bold white]")

    stats_table = Table.grid(padding=(0, 2))
    stats_table.add_column("Stat", style="dim")
    stats_table.add_column("Value", style="bold white")

    stats_table.add_row("Turns played:", str(result.total_turns))
    stats_table.add_row("End reason:", result.end_reason)

    model_labels = model_labels or {}

    if result.is_draw:
        stats_table.add_row("Winner:", "[yellow bold]DRAW![/yellow bold]")
    else:
        winner = fighters_map.get(result.winner or "")
        winner_name = winner.codename if winner else (result.winner or "Unknown")
        winner_model = model_labels.get(result.winner or "", "")
        if winner_model:
            winner_name += f" ({winner_model})"
        stats_table.add_row("Winner:", f"[green bold]{winner_name}![/green bold]")

    stats_table.add_row("Total fumbles:", str(result.total_fumbles))

    console.print(
        Panel(
            stats_table,
            border_style="green" if not result.is_draw else "yellow",
            expand=False,
        )
    )
    console.print("")


def save_replay(result: MatchResult, replay_dir: Path) -> Path:
    """Save the match result as a JSON replay file."""
    replay_dir.mkdir(parents=True, exist_ok=True)
    filename = f"match_{result.match_id[:8]}_{result.total_turns}turns.json"
    path = replay_dir / filename
    path.write_text(json.dumps(serialize_match_result(result), indent=2))
    return path


def serialize_match_result(result: MatchResult) -> dict[str, Any]:
    """Serialize a match result to the CLI replay JSON structure."""
    return result.model_dump(mode="json")


async def turn_callback(
    turn_log: TurnLog,
    fighters: dict[str, Fighter],
    engine: GameEngine,
    model_labels: dict[str, str] | None = None,
) -> None:
    """Callback passed to the engine to print each turn."""
    display_turn(engine, turn_log, fighters, model_labels=model_labels)


_SUPPORTED_PROVIDERS = {"openai", "anthropic"}


def _read_fighter_env(slot: int) -> dict[str, str]:
    prefix = f"FIGHTER{slot}_"
    return {
        "provider": os.environ.get(f"{prefix}PROVIDER", "").strip().lower(),
        "api_key": os.environ.get(f"{prefix}API_KEY", "").strip(),
        "model": os.environ.get(f"{prefix}MODEL", "").strip(),
        "base_url": os.environ.get(f"{prefix}BASE_URL", "").strip(),
    }


def _build_live_clients(fighter_ids: list[str]) -> dict[str, LLMAdapter]:
    from dotenv import load_dotenv

    load_dotenv()

    clients: dict[str, LLMAdapter] = {}
    for idx, fighter_id in enumerate(fighter_ids, start=1):
        cfg = _read_fighter_env(idx)
        label = f"FIGHTER{idx}"

        if not cfg["provider"]:
            raise RuntimeError(
                f"{label}_PROVIDER not set. "
                "Copy backend/.env.example to backend/.env and configure it."
            )
        if cfg["provider"] not in _SUPPORTED_PROVIDERS:
            raise NotImplementedError(
                f"{label}_PROVIDER='{cfg['provider']}' is not yet supported. "
                f"Supported: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
            )
        if not cfg["api_key"]:
            raise RuntimeError(
                f"{label}_API_KEY not set. Fill in your API key in backend/.env."
            )
        if not cfg["model"]:
            raise RuntimeError(
                f"{label}_MODEL not set. "
                "Specify a model ID (e.g. gpt-4.1-mini, claude-sonnet-4-5-20250929) "
                "in backend/.env."
            )

        base_url = cfg["base_url"] or None

        if cfg["provider"] == "openai":
            clients[fighter_id] = OpenAIClient(
                model=cfg["model"],
                api_key=cfg["api_key"],
                base_url=base_url,
            )
        elif cfg["provider"] == "anthropic":
            clients[fighter_id] = AnthropicClient(
                model=cfg["model"],
                api_key=cfg["api_key"],
                base_url=base_url,
            )

    return clients


def _build_cli_fighters(slot_ids: list[str], archetype_ids: list[str]) -> list[Fighter]:
    fighters: list[Fighter] = []
    is_mirror = archetype_ids[0] == archetype_ids[1]

    for index, (slot_id, archetype_id) in enumerate(
        zip(slot_ids, archetype_ids, strict=True)
    ):
        fighter = get_fighter(archetype_id)
        fighter.id = slot_id
        if is_mirror:
            suffix = "A" if index == 0 else "B"
            fighter.codename = f"{fighter.codename} {suffix}"
        fighters.append(fighter)

    fighters[0].position = Position(x=1, y=3)
    fighters[1].position = Position(x=6, y=3)
    return fighters


def _build_cli_state(
    slot_ids: list[str], archetype_ids: list[str], seed: int | None
) -> BattleState:
    fighters = _build_cli_fighters(slot_ids, archetype_ids)
    arena = Arena()
    TerrainGenerator(seed=seed).generate(
        arena,
        start_positions=[fighter.position for fighter in fighters],
    )
    return BattleState(fighters=fighters, arena=arena, phase=MatchPhase.READY)


async def _preflight_check_openai(
    label: str, model: str, api_key: str, base_url: str | None
) -> tuple[bool, str]:
    from importlib import import_module

    openai = import_module("openai")
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": 15.0}
    if base_url:
        kwargs["base_url"] = base_url
    client = openai.AsyncOpenAI(**kwargs)
    started = time.perf_counter()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=4,
        )
        elapsed = time.perf_counter() - started
        text = ""
        if resp.choices and resp.choices[0].message.content:
            text = resp.choices[0].message.content.strip()
        return True, f"OK ({elapsed:.1f}s, replied: {text!r})"
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return False, f"FAILED after {elapsed:.1f}s — {type(exc).__name__}: {exc}"


async def _preflight_check_anthropic(
    label: str, model: str, api_key: str, base_url: str | None
) -> tuple[bool, str]:
    from importlib import import_module

    anthropic = import_module("anthropic")
    kwargs: dict[str, object] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    client = anthropic.AsyncAnthropic(**kwargs)
    started = time.perf_counter()
    try:
        msg = await client.messages.create(
            model=model,
            max_tokens=4,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        elapsed = time.perf_counter() - started
        text = msg.content[0].text.strip() if msg.content else ""
        return True, f"OK ({elapsed:.1f}s, replied: {text!r})"
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return False, f"FAILED after {elapsed:.1f}s — {type(exc).__name__}: {exc}"


async def run_preflight(fighter_ids: list[str]) -> bool:
    from dotenv import load_dotenv

    load_dotenv()

    console.print(f"\n[bold]Pre-flight check …[/bold]")
    all_ok = True

    for idx, fighter_id in enumerate(fighter_ids, start=1):
        cfg = _read_fighter_env(idx)
        label = f"FIGHTER{idx} ({fighter_id})"
        provider = cfg["provider"]
        model = cfg["model"]
        api_key = cfg["api_key"]
        base_url = cfg["base_url"] or None

        console.print(f"  [cyan]{label}[/cyan]: {provider}  model={model}")

        if provider == "openai":
            ok, detail = await _preflight_check_openai(label, model, api_key, base_url)
        elif provider == "anthropic":
            ok, detail = await _preflight_check_anthropic(
                label, model, api_key, base_url
            )
        else:
            ok, detail = False, f"Unsupported provider: {provider}"

        if ok:
            console.print(f"    [green]{detail}[/green]")
        else:
            console.print(f"    [red]{detail}[/red]")
            all_ok = False

    if all_ok:
        console.print(f"  [green bold]All checks passed![/green bold]\n")
    else:
        console.print(
            f"  [red bold]Some checks failed. "
            f"Fix your .env config before running --live.[/red bold]\n"
        )
    return all_ok


async def run_cli_match(
    fighter_ids: list[str],
    use_mock: bool = True,
    max_turns: int = 50,
    seed: int | None = None,
    timeout: float | None = None,
    skip_preflight: bool = False,
    replay_dir: str | Path | None = None,
) -> MatchResult:
    """Run a terminal match and return its result."""
    if replay_dir is None:
        replay_dir = Path("replays")
    elif isinstance(replay_dir, str):
        replay_dir = Path(replay_dir)

    archetype_ids = list(fighter_ids)
    slot_ids = ["fighter_a", "fighter_b"]

    effective_timeout = timeout if timeout is not None else (8.0 if use_mock else 30.0)
    config = MatchConfig(
        fighter_ids=slot_ids,
        max_turns=max_turns,
        seed=seed,
        timeout_per_turn=effective_timeout,
    )

    if use_mock:
        llm_clients = cast(
            dict[str, LLMAdapter],
            {
                fighter_id: MockLLMClient(fighter_id=fighter_id, seed=seed)
                for fighter_id in slot_ids
            },
        )
    else:
        if not skip_preflight:
            preflight_ok = await run_preflight(archetype_ids)
            if not preflight_ok:
                raise RuntimeError(
                    "Pre-flight check failed. Fix your .env and try again, "
                    "or use --no-preflight to skip."
                )
        llm_clients = cast(
            dict[str, LLMAdapter],
            _build_live_clients(slot_ids),
        )

    fighter_a = get_archetype(archetype_ids[0])
    fighter_b = get_archetype(archetype_ids[1])

    # Build model labels for display
    model_labels: dict[str, str] = {}
    if use_mock:
        model_labels = {slot_id: "Mock" for slot_id in slot_ids}
    else:
        from dotenv import load_dotenv

        load_dotenv()
        for idx, fid in enumerate(slot_ids, start=1):
            cfg = _read_fighter_env(idx)
            model_labels[fid] = cfg["model"] or "Unknown"

    a_display = fighter_a.codename
    b_display = fighter_b.codename
    if archetype_ids[0] == archetype_ids[1]:
        a_display += " A"
        b_display += " B"

    a_model = model_labels.get(slot_ids[0], "")
    b_model = model_labels.get(slot_ids[1], "")
    if a_model:
        a_display += f" ({a_model})"
    if b_model:
        b_display += f" ({b_model})"

    console.rule("[bold white]LLM SMASH BROS — 大模型大乱斗[/bold white]")
    console.print(f"  [cyan]{a_display}[/cyan]")
    console.print("    vs")
    console.print(f"  [magenta]{b_display}[/magenta]")
    console.print(
        f"  Max turns: {max_turns} | Mode: {'Mock' if use_mock else 'Live'} | Timeout: {effective_timeout}s"
    )
    console.rule()

    engine = GameEngine(config=config, llm_clients=llm_clients)
    engine.state = _build_cli_state(slot_ids, archetype_ids, seed)
    assert engine.state is not None
    fighters_map = {fighter.id: fighter for fighter in engine.state.fighters}

    async def callback(turn_log: TurnLog) -> None:
        await turn_callback(turn_log, fighters_map, engine, model_labels=model_labels)

    engine.event_callback = callback
    result = await engine.run_match()

    display_match_result(result, fighters_map, model_labels=model_labels)

    # Post-match comments from fighters
    from llm_smash.engine.state import Position

    if not result.is_draw and result.winner:
        winner_client = llm_clients.get(result.winner)
        loser_slots = [sid for sid in slot_ids if sid != result.winner]
        loser_obj = fighters_map.get(loser_slots[0]) if loser_slots else None
        loser_codename = loser_obj.codename if loser_obj is not None else "Unknown"
        if winner_client:
            comment = await winner_client.get_post_match_comment(
                result.winner, loser_codename, "victory"
            )
            if comment:
                winner_obj = fighters_map.get(result.winner)
                display_name = winner_obj.codename if winner_obj else result.winner
                winner_model = model_labels.get(result.winner, "")
                if winner_model:
                    display_name += f" ({winner_model})"
                console.print(
                    f'  [green bold]🏆 {display_name}:[/green bold] [white italic]"{comment}"[/white italic]'
                )
    elif result.is_draw:
        for sid in slot_ids:
            client = llm_clients.get(sid)
            if client:
                opponent_slots = [s for s in slot_ids if s != sid]
                opponent_obj = (
                    fighters_map.get(opponent_slots[0]) if opponent_slots else None
                )
                opp_codename = (
                    opponent_obj.codename if opponent_obj is not None else "Unknown"
                )
                comment = await client.get_post_match_comment(sid, opp_codename, "draw")
                if comment:
                    fighter_obj = fighters_map.get(sid)
                    display_name = fighter_obj.codename if fighter_obj else sid
                    fighter_model = model_labels.get(sid, "")
                    if fighter_model:
                        display_name += f" ({fighter_model})"
                    console.print(
                        f'  [yellow bold]🤝 {display_name}:[/yellow bold] [white italic]"{comment}"[/white italic]'
                    )

    # Save Replay
    saved_path = save_replay(result, replay_dir)
    console.print(f"  [dim]Replay saved to: {saved_path}[/dim]")

    return result

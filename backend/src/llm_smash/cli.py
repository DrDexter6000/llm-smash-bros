"""CLI runner for LLM Smash Bros mock and real matches."""

from __future__ import annotations

import asyncio
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
from llm_smash.engine.state import ActionType, Fighter, MatchResult, TurnEvent, TurnLog
from llm_smash.fighters.roster import get_archetype, get_fighter
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.anthropic_client import AnthropicClient
from llm_smash.llm.mock_client import MockLLMClient
from llm_smash.llm.openai_client import OpenAIClient

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
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


def display_fighter_panel(fighter: Fighter, turn_log: TurnLog | None = None) -> Panel:
    """Render a rich Panel for a single fighter's status and last action."""
    action_text = "None"
    tactical_summary = ""
    trash_talk = ""
    fumbled = False
    fumble_reason = ""

    if turn_log:
        if fighter.id in turn_log.fumbles:
            fumbled = True
            # Fumble reason fallback
            fumble_reason = "Cognitive breakdown"
            resp = turn_log.actions.get(fighter.id)
            if resp and resp.raw_response:
                fumble_reason = resp.raw_response[:100] + (
                    "..." if len(resp.raw_response) > 100 else ""
                )
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

    return Panel(
        content,
        title=f"[{hp_color} bold]{fighter.codename.upper()}[/]",
        title_align="left",
        border_style=hp_color,
    )


def display_turn(
    engine: GameEngine, turn_log: TurnLog, fighters: dict[str, Fighter]
) -> None:
    """Print the full turn display including arena and fighters."""
    assert engine.state is not None

    # Use the first fighter as A, second as B
    perspective_id = engine.state.fighters[0].id if engine.state.fighters else ""
    arena_grid = engine.state.arena.to_ascii_grid(
        engine.state.fighters, perspective_fighter_id=perspective_id
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
        fighter_panels.append(display_fighter_panel(f, turn_log))

    console.rule(f"[bold white]TURN {turn_log.turn_number}[/bold white]")
    console.print(grid_panel)
    for p in fighter_panels:
        console.print(p)
    if events_panel:
        console.print(events_panel)
    console.print("")


def display_match_result(result: MatchResult, fighters_map: dict[str, Fighter]) -> None:
    """Print the final match outcome statistics."""
    console.rule("[bold white]MATCH COMPLETE[/bold white]")

    stats_table = Table.grid(padding=(0, 2))
    stats_table.add_column("Stat", style="dim")
    stats_table.add_column("Value", style="bold white")

    stats_table.add_row("Turns played:", str(result.total_turns))
    stats_table.add_row("End reason:", result.end_reason)

    if result.is_draw:
        stats_table.add_row("Winner:", "[yellow bold]DRAW![/yellow bold]")
    else:
        winner = fighters_map.get(result.winner or "")
        winner_name = winner.codename if winner else result.winner
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
    path.write_text(result.model_dump_json(indent=2))
    return path


async def turn_callback(
    turn_log: TurnLog, fighters: dict[str, Fighter], engine: GameEngine
) -> None:
    """Callback passed to the engine to print each turn."""
    display_turn(engine, turn_log, fighters)


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

    effective_timeout = timeout if timeout is not None else (8.0 if use_mock else 30.0)
    config = MatchConfig(
        fighter_ids=fighter_ids,
        max_turns=max_turns,
        seed=seed,
        timeout_per_turn=effective_timeout,
    )

    if use_mock:
        llm_clients = cast(
            dict[str, LLMAdapter],
            {
                fighter_id: MockLLMClient(fighter_id=fighter_id, seed=seed)
                for fighter_id in fighter_ids
            },
        )
    else:
        if not skip_preflight:
            preflight_ok = await run_preflight(fighter_ids)
            if not preflight_ok:
                raise RuntimeError(
                    "Pre-flight check failed. Fix your .env and try again, "
                    "or use --no-preflight to skip."
                )
        llm_clients = cast(
            dict[str, LLMAdapter],
            _build_live_clients(fighter_ids),
        )

    fighter_a = get_archetype(fighter_ids[0])
    fighter_b = get_archetype(fighter_ids[1])

    console.rule("[bold white]LLM SMASH BROS — 大模型大乱斗[/bold white]")
    console.print(f"  [cyan]{fighter_a.codename}[/cyan] ({fighter_a.id})")
    console.print("    vs")
    console.print(f"  [magenta]{fighter_b.codename}[/magenta] ({fighter_b.id})")
    console.print(
        f"  Max turns: {max_turns} | Mode: {'Mock' if use_mock else 'Live'} | Timeout: {effective_timeout}s"
    )
    console.rule()

    engine = GameEngine(config=config, llm_clients=llm_clients)
    engine._ensure_state()
    assert engine.state is not None
    fighters_map = {fighter.id: fighter for fighter in engine.state.fighters}

    async def callback(turn_log: TurnLog) -> None:
        await turn_callback(turn_log, fighters_map, engine)

    engine.event_callback = callback
    result = await engine.run_match()

    display_match_result(result, fighters_map)

    # Save Replay
    saved_path = save_replay(result, replay_dir)
    console.print(f"  [dim]Replay saved to: {saved_path}[/dim]")

    return result

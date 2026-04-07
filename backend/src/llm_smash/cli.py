"""CLI runner for LLM Smash Bros mock and real matches."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Any, cast

from llm_smash.engine.game import GameEngine, MatchConfig
from llm_smash.engine.state import ActionType, Fighter, MatchResult, TurnEvent, TurnLog
from llm_smash.fighters.roster import get_archetype, get_fighter
from llm_smash.llm.adapter import LLMAdapter
from llm_smash.llm.anthropic_client import AnthropicClient
from llm_smash.llm.mock_client import MockLLMClient
from llm_smash.llm.openai_client import OpenAIClient

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def safe_print(message: str = "") -> None:
    """Print text without crashing on non-Unicode Windows terminals."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sys.stdout.write(f"{message}\n")
    except UnicodeEncodeError:
        sanitized = message.encode(encoding, errors="replace").decode(
            encoding, errors="replace"
        )
        sys.stdout.write(f"{sanitized}\n")


def hp_bar(hp: int, max_hp: int, width: int = 20) -> str:
    """Render an ASCII HP bar."""
    ratio = hp / max_hp if max_hp > 0 else 0
    filled = int(width * ratio)
    empty = width - filled
    color = GREEN if ratio > 0.5 else YELLOW if ratio > 0.25 else RED
    return f"{color}[{'█' * filled}{'░' * empty}]{RESET} {hp}/{max_hp}"


def energy_bar(energy: int, max_energy: int) -> str:
    """Render an energy bar."""
    return f"{CYAN}⚡{energy}/{max_energy}{RESET}"


async def turn_callback(turn_log: TurnLog, fighters: dict[str, Fighter]) -> None:
    """Print a single turn summary to stdout."""
    safe_print(f"\n{BOLD}═══ Turn {turn_log.turn_number} ═══{RESET}")

    for fighter in fighters.values():
        safe_print(
            f"  {BOLD}{fighter.codename}{RESET}: "
            f"{hp_bar(fighter.hp, fighter.max_hp)} "
            f"{energy_bar(fighter.energy, fighter.max_energy)}"
        )

    for fumble_id in turn_log.fumbles:
        fighter = fighters.get(fumble_id)
        name = fighter.codename if fighter else fumble_id
        safe_print(f"  {RED}💥 {name} FUMBLED!{RESET}")

    for fighter_id, response in turn_log.actions.items():
        if response is None:
            continue
        fighter = fighters.get(fighter_id)
        name = fighter.codename if fighter else fighter_id
        action_type = response.action.get("type", "?")

        if action_type == ActionType.ATTACK.value:
            ability_name = response.action.get("ability", "?")
            safe_print(f"  {MAGENTA}⚔️  {name} uses {ability_name}{RESET}")
        elif action_type == ActionType.DEFEND.value:
            safe_print(f"  {BLUE}🛡️  {name} defends{RESET}")
        elif action_type == ActionType.WAIT.value:
            safe_print(f"  {DIM}⏳ {name} waits{RESET}")

    for event in turn_log.events:
        _print_event(event)

    for fighter_id, response in turn_log.actions.items():
        if response is None or not response.trash_talk:
            continue
        fighter = fighters.get(fighter_id)
        name = fighter.codename if fighter else fighter_id
        if response.tactical_summary:
            safe_print(f"  {DIM}🧠 {name}: {response.tactical_summary}{RESET}")
        safe_print(f'  {DIM}💬 {name}: "{response.trash_talk}"{RESET}')


def _print_event(event: TurnEvent) -> None:
    if event.type == "damage":
        safe_print(f"  {RED}💥 {event.description}{RESET}")
    elif event.type == "ko":
        safe_print(f"  {RED}{BOLD}☠️  {event.description}{RESET}")
    elif event.type == "hazard" and event.source_id == "arena":
        safe_print(f"  {YELLOW}⚠️  {event.description}{RESET}")


_SUPPORTED_PROVIDERS = {"openai", "anthropic"}


def _read_fighter_env(slot: int) -> dict[str, str]:
    """Read FIGHTER{slot}_* environment variables into a dict.

    Returns keys: provider, api_key, model, base_url (all lowercase).
    Missing values default to empty strings.
    """
    prefix = f"FIGHTER{slot}_"
    return {
        "provider": os.environ.get(f"{prefix}PROVIDER", "").strip().lower(),
        "api_key": os.environ.get(f"{prefix}API_KEY", "").strip(),
        "model": os.environ.get(f"{prefix}MODEL", "").strip(),
        "base_url": os.environ.get(f"{prefix}BASE_URL", "").strip(),
    }


def _build_live_clients(fighter_ids: list[str]) -> dict[str, LLMAdapter]:
    """Instantiate real LLM clients from FIGHTER1_*/FIGHTER2_* env vars.

    Each fighter slot is independently configurable with its own provider,
    api_key, model, and optional base_url.  Raises immediately with a
    human-readable message if required values are missing.
    """
    from dotenv import load_dotenv

    load_dotenv()  # idempotent — safe to call multiple times

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
    """Send a tiny chat completion to verify an OpenAI-compatible endpoint."""
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
    """Send a tiny message to verify an Anthropic endpoint."""
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
    """Validate every fighter's API config with a lightweight probe.

    Returns True if all checks pass, False otherwise.
    """
    from dotenv import load_dotenv

    load_dotenv()

    safe_print(f"\n{BOLD}Pre-flight check …{RESET}")
    all_ok = True

    for idx, fighter_id in enumerate(fighter_ids, start=1):
        cfg = _read_fighter_env(idx)
        label = f"FIGHTER{idx} ({fighter_id})"
        provider = cfg["provider"]
        model = cfg["model"]
        api_key = cfg["api_key"]
        base_url = cfg["base_url"] or None

        safe_print(f"  {CYAN}{label}{RESET}: {provider}  model={model}")

        if provider == "openai":
            ok, detail = await _preflight_check_openai(label, model, api_key, base_url)
        elif provider == "anthropic":
            ok, detail = await _preflight_check_anthropic(
                label, model, api_key, base_url
            )
        else:
            ok, detail = False, f"Unsupported provider: {provider}"

        if ok:
            safe_print(f"    {GREEN}{detail}{RESET}")
        else:
            safe_print(f"    {RED}{detail}{RESET}")
            all_ok = False

    if all_ok:
        safe_print(f"  {GREEN}{BOLD}All checks passed!{RESET}\n")
    else:
        safe_print(
            f"  {RED}{BOLD}Some checks failed. "
            f"Fix your .env config before running --live.{RESET}\n"
        )
    return all_ok


async def run_cli_match(
    fighter_ids: list[str],
    use_mock: bool = True,
    max_turns: int = 50,
    seed: int | None = None,
    timeout: float | None = None,
    skip_preflight: bool = False,
) -> MatchResult:
    """Run a terminal match and return its result."""
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
        # Auto-run preflight for live matches unless explicitly skipped
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

    safe_print(f"\n{BOLD}{'═' * 50}{RESET}")
    safe_print(f"{BOLD}  LLM SMASH BROS — 大模型大乱斗{RESET}")
    safe_print(f"{BOLD}{'═' * 50}{RESET}")
    safe_print(f"  {CYAN}{fighter_a.codename}{RESET} ({fighter_a.id})")
    safe_print("    vs")
    safe_print(f"  {MAGENTA}{fighter_b.codename}{RESET} ({fighter_b.id})")
    safe_print(
        f"  Max turns: {max_turns} | Mode: {'Mock' if use_mock else 'Live'} | Timeout: {effective_timeout}s"
    )
    safe_print(f"{BOLD}{'═' * 50}{RESET}")

    engine = GameEngine(config=config, llm_clients=llm_clients)
    engine._ensure_state()
    assert engine.state is not None
    fighters_map = {fighter.id: fighter for fighter in engine.state.fighters}

    async def callback(turn_log: TurnLog) -> None:
        await turn_callback(turn_log, fighters_map)

    engine.event_callback = callback
    result = await engine.run_match()

    safe_print(f"\n{BOLD}{'═' * 50}{RESET}")
    safe_print(f"{BOLD}  MATCH COMPLETE{RESET}")
    safe_print(f"{BOLD}{'═' * 50}{RESET}")
    safe_print(f"  Turns played: {result.total_turns}")
    safe_print(f"  End reason: {result.end_reason}")
    if result.is_draw:
        safe_print(f"  {YELLOW}{BOLD}DRAW!{RESET}")
    else:
        winner = fighters_map.get(result.winner or "")
        winner_name = winner.codename if winner else result.winner
        safe_print(f"  {GREEN}{BOLD}WINNER: {winner_name}!{RESET}")
    safe_print(f"  Total fumbles: {result.total_fumbles}")
    safe_print(f"{BOLD}{'═' * 50}{RESET}\n")

    return result

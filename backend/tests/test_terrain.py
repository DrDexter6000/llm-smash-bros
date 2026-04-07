"""Tests for terrain generation and ASCII arena rendering."""

# pyright: reportMissingImports=false

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm_smash.engine.state import Arena, Fighter, Hazard, Position, TerrainType


def _make_fighter(fighter_id: str, x: int, y: int) -> Fighter:
    return Fighter(
        id=fighter_id,
        codename=fighter_id.title(),
        hp=100,
        max_hp=100,
        energy=100,
        max_energy=100,
        position=Position(x=x, y=y),
        abilities=[],
    )


def test_terrain_generator_creates_symmetric_connected_layout():
    from llm_smash.engine.terrain import TerrainGenerator

    arena = Arena(width=8, height=6)
    starts = [Position(x=1, y=3), Position(x=6, y=3)]

    TerrainGenerator(seed=42).generate(arena, start_positions=starts)

    assert 7 <= len(arena.terrain) <= 12
    for key, value in arena.terrain.items():
        x_str, y_str = key.split(",")
        mirror_key = f"{arena.width - 1 - int(x_str)},{int(y_str)}"
        assert arena.terrain.get(mirror_key) == value

    for start in starts:
        assert arena.get_terrain_at(start) == TerrainType.OPEN

    assert arena.is_passable(starts[0])
    assert arena.is_passable(starts[1])


def test_terrain_generator_keeps_start_and_adjacent_tiles_clear():
    from llm_smash.engine.terrain import TerrainGenerator

    arena = Arena(width=8, height=6)
    starts = [Position(x=1, y=3), Position(x=6, y=3)]

    TerrainGenerator(seed=7).generate(arena, start_positions=starts)

    blocked = {
        (pos.x + dx, pos.y + dy)
        for pos in starts
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if 0 <= pos.x + dx < arena.width and 0 <= pos.y + dy < arena.height
    }
    terrain_positions = {tuple(map(int, key.split(","))) for key in arena.terrain}

    assert terrain_positions.isdisjoint(blocked)


def test_terrain_generator_stays_within_density_band_across_sample_seeds():
    from llm_smash.engine.terrain import TerrainGenerator

    starts = [Position(x=1, y=3), Position(x=6, y=3)]

    for seed in range(10):
        arena = Arena(width=8, height=6)
        TerrainGenerator(seed=seed).generate(arena, start_positions=starts)
        assert 7 <= len(arena.terrain) <= 12


def test_ascii_grid_renders_terrain_fighters_and_hazards():
    arena = Arena(
        width=8,
        height=6,
        terrain={
            "2,1": TerrainType.HIGH_GROUND.value,
            "5,1": TerrainType.COVER.value,
            "1,2": TerrainType.RIFT.value,
            "6,2": TerrainType.RIFT.value,
        },
        hazards=[
            Hazard(
                type="firewall",
                position=Position(x=3, y=1),
                damage=8,
                turns_remaining=2,
            )
        ],
    )
    fighters = [_make_fighter("alpha", 1, 3), _make_fighter("beta", 6, 3)]

    grid = arena.to_ascii_grid(fighters=fighters, perspective_fighter_id="alpha")

    assert "Arena (8x6):" in grid
    assert "  01234567" in grid
    assert "1 ..H..C.." in grid
    assert "2 .#....#." in grid
    assert "3 .A....B." in grid
    assert "A=You  B=Opponent" in grid
    assert "H=High Ground  C=Cover  #=Rift  .=Open" in grid
    assert "Hazards: firewall@(3,1)[2t]" in grid

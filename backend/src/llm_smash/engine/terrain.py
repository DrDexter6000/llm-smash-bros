"""Terrain generation for symmetric tactical arena layouts."""

from __future__ import annotations

import random
from collections import deque

from llm_smash.engine.state import Arena, Position, TerrainType


class TerrainGenerator:
    """Populate arenas with symmetric, seedable terrain."""

    def __init__(self, seed: int | None = None):
        self._seed = seed
        self._rng = random.Random(seed)

    def generate(self, arena: Arena, start_positions: list[Position]) -> None:
        """Populate arena.terrain with symmetric random placement."""
        start_keys = {(pos.x, pos.y) for pos in start_positions}
        protected = {
            (pos.x + dx, pos.y + dy)
            for pos in start_positions
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if 0 <= pos.x + dx < arena.width and 0 <= pos.y + dy < arena.height
        }

        for offset in range(10):
            terrain = self._generate_candidate(arena, protected)
            arena.terrain = terrain
            if start_keys.issubset(
                {(p.x, p.y) for p in start_positions}
            ) and self._is_connected(arena, start_positions[0], start_positions[1]):
                return
            if self._seed is not None:
                self._rng = random.Random(self._seed + offset + 1)

        arena.terrain = {}

    def _generate_candidate(
        self, arena: Arena, protected: set[tuple[int, int]]
    ) -> dict[str, str]:
        terrain: dict[str, str] = {}
        target_tiles = self._normalize_target_tiles(self._rng.randint(7, 12))
        min_rifts = 2 if target_tiles >= 8 else 0
        rifts_placed = 0
        left_side = [
            (x, y)
            for x in range(arena.width // 2)
            for y in range(arena.height)
            if (x, y) not in protected and (arena.width - 1 - x, y) not in protected
        ]
        self._rng.shuffle(left_side)

        for x, y in left_side:
            mirrored = (arena.width - 1 - x, y)
            tiles_added = 1 if mirrored == (x, y) else 2
            if len(terrain) + tiles_added > target_tiles:
                continue
            remaining_slots = target_tiles - len(terrain)
            terrain_type = self._choose_terrain_type(
                remaining_slots=remaining_slots,
                min_rifts=min_rifts,
                rifts_placed=rifts_placed,
            )
            terrain[f"{x},{y}"] = terrain_type.value
            if mirrored != (x, y):
                terrain[f"{mirrored[0]},{mirrored[1]}"] = terrain_type.value
            if terrain_type == TerrainType.RIFT:
                rifts_placed += tiles_added
            if len(terrain) >= target_tiles:
                break

        return terrain

    def _normalize_target_tiles(self, requested_tiles: int) -> int:
        """Return an achievable mirrored tile count for an even-width arena."""
        if requested_tiles % 2 == 1:
            requested_tiles += 1
        return max(8, min(12, requested_tiles))

    def _choose_terrain_type(
        self, *, remaining_slots: int, min_rifts: int, rifts_placed: int
    ) -> TerrainType:
        if remaining_slots <= (min_rifts - rifts_placed):
            return TerrainType.RIFT
        roll = self._rng.random()
        if roll < 0.4:
            return TerrainType.HIGH_GROUND
        if roll < 0.8:
            return TerrainType.COVER
        return TerrainType.RIFT

    def _is_connected(self, arena: Arena, start: Position, goal: Position) -> bool:
        queue = deque([start])
        seen = {(start.x, start.y)}

        while queue:
            current = queue.popleft()
            if current == goal:
                return True

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = Position(x=current.x + dx, y=current.y + dy)
                key = (nxt.x, nxt.y)
                if key in seen or not arena.is_passable(nxt):
                    continue
                seen.add(key)
                queue.append(nxt)

        return False

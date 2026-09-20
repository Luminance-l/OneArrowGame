"""Hand-authored levels and validation helpers.

The layouts are original and contain no material from the commercial reference game.
"""

from __future__ import annotations

from dataclasses import dataclass

from constants import Direction


@dataclass(frozen=True, slots=True)
class Level:
    name: str
    size: int
    layout: tuple[tuple[str | None, ...], ...]
    par_time: int


def _grid(size: int, arrows: dict[tuple[int, int], str]) -> tuple[tuple[str | None, ...], ...]:
    return tuple(
        tuple(arrows.get((row, col)) for col in range(size))
        for row in range(size)
    )


LEVELS: tuple[Level, ...] = (
    Level(
        "初见 · 四向",
        5,
        _grid(5, {
            (0, 2): "UP", (1, 0): "LEFT", (2, 2): "RIGHT",
            (2, 4): "RIGHT", (4, 1): "DOWN", (3, 3): "LEFT",
        }),
        25,
    ),
    Level(
        "交错 · 留白",
        6,
        _grid(6, {
            (0, 1): "UP", (0, 4): "RIGHT", (1, 2): "DOWN",
            (2, 0): "LEFT", (2, 2): "RIGHT", (2, 5): "DOWN",
            (3, 1): "UP", (3, 4): "LEFT", (5, 0): "DOWN",
            (5, 3): "RIGHT",
        }),
        45,
    ),
    Level(
        "回声 · 回廊",
        7,
        _grid(7, {
            (0, 0): "UP", (0, 3): "LEFT", (0, 6): "RIGHT",
            (1, 2): "DOWN", (1, 5): "UP", (2, 0): "LEFT",
            (2, 3): "RIGHT", (2, 6): "DOWN", (3, 1): "UP",
            (3, 4): "LEFT", (4, 0): "DOWN", (4, 2): "RIGHT",
            (4, 5): "UP", (5, 3): "LEFT", (6, 1): "DOWN",
        }),
        70,
    ),
    Level(
        "棱镜 · 逆光",
        7,
        _grid(7, {
            (0, 1): "LEFT", (0, 4): "UP", (1, 0): "DOWN",
            (1, 3): "RIGHT", (1, 6): "UP", (2, 2): "LEFT",
            (2, 5): "DOWN", (3, 0): "LEFT", (3, 3): "UP",
            (3, 6): "RIGHT", (4, 1): "DOWN", (4, 4): "LEFT",
            (5, 0): "DOWN", (5, 3): "RIGHT", (5, 6): "UP",
            (6, 2): "LEFT", (6, 5): "DOWN",
        }),
        85,
    ),
    Level(
        "终章 · 星阵",
        8,
        _grid(8, {
            (0, 0): "UP", (0, 2): "LEFT", (0, 5): "UP", (0, 7): "RIGHT",
            (1, 1): "DOWN", (1, 4): "RIGHT", (1, 6): "UP",
            (2, 0): "LEFT", (2, 3): "RIGHT", (2, 5): "DOWN",
            (3, 1): "LEFT", (3, 4): "LEFT", (3, 7): "RIGHT",
            (4, 0): "DOWN", (4, 2): "RIGHT", (4, 6): "UP",
            (5, 1): "LEFT", (5, 3): "DOWN", (5, 5): "RIGHT",
            (6, 0): "DOWN", (6, 4): "LEFT", (6, 7): "UP",
            (7, 2): "LEFT", (7, 5): "DOWN",
        }),
        110,
    ),
)


def validate_levels() -> None:
    """Fail fast when level data contains an invalid direction or shape."""
    for number, level in enumerate(LEVELS, start=1):
        if len(level.layout) != level.size:
            raise ValueError(f"Level {number}: wrong row count")
        for row in level.layout:
            if len(row) != level.size:
                raise ValueError(f"Level {number}: wrong column count")
            for item in row:
                if item is not None:
                    Direction(item)


validate_levels()

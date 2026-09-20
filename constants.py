"""Shared constants for One Arrow Game."""

from __future__ import annotations

from enum import Enum


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]

    @property
    def symbol(self) -> str:
        return {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.LEFT: "←",
            Direction.RIGHT: "→",
        }[self]


class GameStatus(str, Enum):
    PLAYING = "PLAYING"
    CLEARED = "CLEARED"
    FAILED = "FAILED"


WINDOW_SIZE = (1000, 760)
FPS = 60
MAX_MISTAKES = 3


"""Arrow domain object."""

from __future__ import annotations

from dataclasses import dataclass

from constants import Direction


@dataclass(frozen=True, slots=True)
class Arrow:
    row: int
    col: int
    direction: Direction

    def moved(self, row: int, col: int) -> "Arrow":
        return Arrow(row, col, self.direction)


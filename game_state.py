"""Pure, testable game rules for One Arrow Game."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from arrow import Arrow
from constants import Direction, GameStatus, MAX_MISTAKES
from level import LEVELS, Level


@dataclass(frozen=True, slots=True)
class MoveResult:
    kind: str
    arrow: Arrow | None = None
    blocker: Arrow | None = None


@dataclass(slots=True)
class Snapshot:
    arrows: dict[tuple[int, int], Arrow]
    mistakes: int
    score: int
    status: GameStatus
    hints_used: int


class GameState:
    def __init__(self, level_index: int = 0, max_mistakes: int = MAX_MISTAKES):
        self.max_mistakes = max_mistakes
        self.level_index = level_index
        self.level: Level = LEVELS[level_index]
        self.arrows: dict[tuple[int, int], Arrow] = {}
        self.mistakes = max_mistakes
        self.score = 0
        self.status = GameStatus.PLAYING
        self.hints_used = 0
        self.history: list[Snapshot] = []
        self.restart()

    def restart(self) -> None:
        self.level = LEVELS[self.level_index]
        self.arrows = {
            (row, col): Arrow(row, col, Direction(value))
            for row, line in enumerate(self.level.layout)
            for col, value in enumerate(line)
            if value is not None
        }
        self.mistakes = self.max_mistakes
        self.score = 0
        self.status = GameStatus.PLAYING
        self.hints_used = 0
        self.history = []

    def load_level(self, level_index: int) -> None:
        if not 0 <= level_index < len(LEVELS):
            raise IndexError("level index out of range")
        self.level_index = level_index
        self.restart()

    @property
    def remaining(self) -> int:
        return len(self.arrows)

    def _first_blocker(self, arrow: Arrow) -> Arrow | None:
        dr, dc = arrow.direction.delta
        row, col = arrow.row + dr, arrow.col + dc
        while 0 <= row < self.level.size and 0 <= col < self.level.size:
            blocker = self.arrows.get((row, col))
            if blocker is not None:
                return blocker
            row += dr
            col += dc
        return None

    def can_exit(self, row: int, col: int) -> bool:
        arrow = self.arrows.get((row, col))
        return arrow is not None and self._first_blocker(arrow) is None

    def blocker_for(self, row: int, col: int) -> Arrow | None:
        """Return the first visible blocker for UI explanations, if any."""
        arrow = self.arrows.get((row, col))
        return self._first_blocker(arrow) if arrow is not None else None

    def _remember(self) -> None:
        self.history.append(Snapshot(
            self.arrows.copy(), self.mistakes, self.score, self.status, self.hints_used
        ))

    def click(self, row: int, col: int) -> MoveResult:
        if self.status is not GameStatus.PLAYING:
            return MoveResult("ignored")
        arrow = self.arrows.get((row, col))
        if arrow is None:
            return MoveResult("empty")

        self._remember()
        blocker = self._first_blocker(arrow)
        if blocker is not None:
            self.mistakes -= 1
            self.score = max(0, self.score - 25)
            if self.mistakes <= 0:
                self.status = GameStatus.FAILED
            return MoveResult("blocked", arrow, blocker)

        del self.arrows[(row, col)]
        self.score += 100
        if not self.arrows:
            self.status = GameStatus.CLEARED
        return MoveResult("removed", arrow)

    def undo(self) -> bool:
        if not self.history:
            return False
        previous = self.history.pop()
        self.arrows = previous.arrows
        self.mistakes = previous.mistakes
        self.score = previous.score
        self.status = previous.status
        self.hints_used = previous.hints_used
        return True

    def safe_arrows(self) -> list[Arrow]:
        return [arrow for arrow in self.arrows.values() if self._first_blocker(arrow) is None]

    def hint(self) -> Arrow | None:
        solution = solve(self.arrows.values(), self.level.size)
        if not solution:
            return None
        self.hints_used += 1
        return self.arrows[solution[0]]


def _is_safe(
    position: tuple[int, int],
    direction: Direction,
    occupied: frozenset[tuple[int, int]],
    size: int,
) -> bool:
    dr, dc = direction.delta
    row, col = position[0] + dr, position[1] + dc
    while 0 <= row < size and 0 <= col < size:
        if (row, col) in occupied:
            return False
        row += dr
        col += dc
    return True


def solve(arrows: Iterable[Arrow], size: int) -> list[tuple[int, int]] | None:
    """Return a shortest valid removal sequence using breadth-first search."""
    directions = {(a.row, a.col): a.direction for a in arrows}
    start = frozenset(directions)
    queue = deque([(start, [])])
    visited = {start}
    while queue:
        occupied, path = queue.popleft()
        if not occupied:
            return path
        for position in sorted(occupied):
            if not _is_safe(position, directions[position], occupied, size):
                continue
            next_state = occupied - {position}
            if next_state not in visited:
                visited.add(next_state)
                queue.append((next_state, path + [position]))
    return None


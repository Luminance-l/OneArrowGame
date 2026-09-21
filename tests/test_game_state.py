"""Automated acceptance and regression tests for the game rules."""

from __future__ import annotations

import unittest
import wave
from pathlib import Path

from arrow import Arrow
from constants import Direction, GameStatus
from game_state import GameState, solve
from level import LEVELS


class GameStateAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = GameState(0)

    def test_t01_unblocked_arrow_flies_out(self) -> None:
        before = self.game.remaining
        result = self.game.click(0, 2)
        self.assertEqual("removed", result.kind)
        self.assertEqual(before - 1, self.game.remaining)

    def test_t02_blocked_arrow_costs_one_mistake(self) -> None:
        before = self.game.mistakes
        result = self.game.click(2, 2)  # RIGHT is blocked by the arrow at (2, 4)
        self.assertEqual("blocked", result.kind)
        self.assertEqual(before - 1, self.game.mistakes)
        self.assertIn((2, 2), self.game.arrows)

    def test_t03_edge_arrow_has_no_out_of_bounds_error(self) -> None:
        result = self.game.click(1, 0)
        self.assertEqual("removed", result.kind)
        self.assertNotIn((1, 0), self.game.arrows)

    def test_t04_clearing_every_arrow_completes_level(self) -> None:
        sequence = solve(self.game.arrows.values(), self.game.level.size)
        self.assertIsNotNone(sequence)
        for row, col in sequence or []:
            self.assertEqual("removed", self.game.click(row, col).kind)
        self.assertEqual(GameStatus.CLEARED, self.game.status)
        self.assertEqual(0, self.game.remaining)

    def test_t05_mistakes_exhausted_shows_failure_state(self) -> None:
        for _ in range(self.game.max_mistakes):
            self.game.click(2, 2)
        self.assertEqual(GameStatus.FAILED, self.game.status)

    def test_t06_restart_restores_layout_and_mistakes(self) -> None:
        original = self.game.arrows.copy()
        self.game.click(0, 2)
        self.game.click(2, 2)
        self.game.restart()
        self.assertEqual(original, self.game.arrows)
        self.assertEqual(self.game.max_mistakes, self.game.mistakes)
        self.assertEqual(GameStatus.PLAYING, self.game.status)


class DirectionAndExtraFeatureTests(unittest.TestCase):
    def test_original_audio_assets_are_valid_wav_files(self) -> None:
        audio_dir = Path(__file__).resolve().parents[1] / "assets" / "audio"
        for name in ("background", "launch", "wrong", "failure", "clear", "button"):
            with self.subTest(name=name), wave.open(str(audio_dir / f"{name}.wav"), "rb") as stream:
                self.assertEqual(1, stream.getnchannels())
                self.assertEqual(2, stream.getsampwidth())
                self.assertEqual(22_050, stream.getframerate())
                self.assertGreater(stream.getnframes(), 2_000)

    def test_all_four_directions_scan_correctly(self) -> None:
        game = GameState(0)
        game.level = LEVELS[0]
        cases = {
            Direction.UP: (2, 2, (0, 2)),
            Direction.DOWN: (2, 2, (4, 2)),
            Direction.LEFT: (2, 2, (2, 0)),
            Direction.RIGHT: (2, 2, (2, 4)),
        }
        for direction, (row, col, blocker_pos) in cases.items():
            with self.subTest(direction=direction):
                game.arrows = {
                    (row, col): Arrow(row, col, direction),
                    blocker_pos: Arrow(*blocker_pos, Direction.UP),
                }
                self.assertFalse(game.can_exit(row, col))
                del game.arrows[blocker_pos]
                self.assertTrue(game.can_exit(row, col))

    def test_undo_restores_successful_and_failed_moves(self) -> None:
        game = GameState(0)
        original = game.arrows.copy()
        game.click(0, 2)
        self.assertTrue(game.undo())
        self.assertEqual(original, game.arrows)
        game.click(2, 2)
        self.assertTrue(game.undo())
        self.assertEqual(game.max_mistakes, game.mistakes)

    def test_hint_is_always_safe(self) -> None:
        game = GameState(2)
        hint = game.hint()
        self.assertIsNotNone(hint)
        self.assertTrue(game.can_exit(hint.row, hint.col))

    def test_reasoning_view_can_explain_first_blocker(self) -> None:
        game = GameState(0)
        blocker = game.blocker_for(2, 2)
        self.assertIsNotNone(blocker)
        self.assertEqual((2, 4), (blocker.row, blocker.col))
        self.assertIsNone(game.blocker_for(0, 2))

    def test_every_level_is_solvable_and_uses_all_directions(self) -> None:
        for index, level in enumerate(LEVELS):
            with self.subTest(level=index + 1):
                game = GameState(index)
                sequence = solve(game.arrows.values(), level.size)
                self.assertIsNotNone(sequence)
                self.assertEqual(len(game.arrows), len(sequence or []))
                directions = {arrow.direction for arrow in game.arrows.values()}
                self.assertEqual(set(Direction), directions)


if __name__ == "__main__":
    unittest.main()

"""Entry point for One Arrow Game."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

from arrow import Arrow
from constants import FPS, GameStatus, WINDOW_SIZE
from game_state import GameState
from level import LEVELS
from ui import (
    CORAL, CYAN, GOLD, INK, LAVENDER, MUTED, PANEL, Button,
    draw_arrow, draw_background,
)


BASE_DIR = Path(__file__).resolve().parent
SAVE_PATH = BASE_DIR / ".one_arrow_save.json"


@dataclass(slots=True)
class FlyingArrow:
    arrow: Arrow
    x: float
    y: float
    life: float = 0.48


class GameApp:
    def __init__(self, headless: bool = False):
        pygame.init()
        pygame.display.set_caption("一箭又一箭 · One Arrow Game")
        self.surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = self._load_fonts()
        self.scene = "start"
        self.state = GameState()
        self.running = True
        self.started_at = pygame.time.get_ticks()
        self.flying: list[FlyingArrow] = []
        self.blocked_at = 0
        self.blocked_pos: tuple[int, int] | None = None
        self.hint_pos: tuple[int, int] | None = None
        self.hint_at = 0
        self.toast = ""
        self.toast_at = 0
        self.unlocked, self.best_scores = self._load_progress()
        self.headless = headless

    @staticmethod
    def _font_candidates() -> list[str]:
        return ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial"]

    def _load_fonts(self) -> dict[str, pygame.font.Font]:
        name = next((n for n in self._font_candidates() if pygame.font.match_font(n)), None)
        return {
            "hero": pygame.font.SysFont(name, 62, bold=True),
            "title": pygame.font.SysFont(name, 34, bold=True),
            "h2": pygame.font.SysFont(name, 24, bold=True),
            "body": pygame.font.SysFont(name, 18),
            "small": pygame.font.SysFont(name, 14),
        }

    @staticmethod
    def _load_progress() -> tuple[int, dict[str, int]]:
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            return max(1, min(len(LEVELS), int(data.get("unlocked", 1)))), data.get("best_scores", {})
        except (OSError, ValueError, TypeError):
            return 1, {}

    def _save_progress(self) -> None:
        data = {"unlocked": self.unlocked, "best_scores": self.best_scores}
        SAVE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def start_level(self, index: int) -> None:
        if index >= self.unlocked:
            return
        self.state.load_level(index)
        self.scene = "game"
        self.started_at = pygame.time.get_ticks()
        self.flying.clear()
        self.blocked_pos = None
        self.hint_pos = None

    def elapsed(self) -> int:
        return max(0, (pygame.time.get_ticks() - self.started_at) // 1000)

    def stars(self) -> int:
        stars = 3
        if self.state.mistakes < self.state.max_mistakes:
            stars -= 1
        if self.elapsed() > self.state.level.par_time or self.state.hints_used > 0:
            stars -= 1
        return max(1, stars)

    def board_geometry(self) -> tuple[pygame.Rect, float]:
        board_size = 570
        rect = pygame.Rect(56, 132, board_size, board_size)
        return rect, board_size / self.state.level.size

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        board, cell = self.board_geometry()
        return board.left + (col + .5) * cell, board.top + (row + .5) * cell

    def cell_at(self, position: tuple[int, int]) -> tuple[int, int] | None:
        board, cell = self.board_geometry()
        if not board.collidepoint(position):
            return None
        col = int((position[0] - board.left) / cell)
        row = int((position[1] - board.top) / cell)
        return row, col

    def handle_game_click(self, position: tuple[int, int]) -> None:
        buttons = self.game_buttons()
        if buttons[0].hit(position):
            self.state.restart()
            self.started_at = pygame.time.get_ticks()
            self.flying.clear()
            return
        if buttons[1].hit(position):
            if self.state.undo():
                self.toast_message("已撤销上一步")
            else:
                self.toast_message("暂无可撤销操作")
            return
        if buttons[2].hit(position):
            hint = self.state.hint()
            if hint:
                self.hint_pos = (hint.row, hint.col)
                self.hint_at = pygame.time.get_ticks()
                self.toast_message("AI 已标出安全箭头")
            return
        if buttons[3].hit(position):
            self.scene = "levels"
            return

        cell = self.cell_at(position)
        if cell is None:
            return
        result = self.state.click(*cell)
        now = pygame.time.get_ticks()
        if result.kind == "removed" and result.arrow:
            x, y = self.cell_center(result.arrow.row, result.arrow.col)
            self.flying.append(FlyingArrow(result.arrow, x, y))
            self.hint_pos = None
            if self.state.status is GameStatus.CLEARED:
                self._complete_level()
        elif result.kind == "blocked" and result.arrow:
            self.blocked_pos = (result.arrow.row, result.arrow.col)
            self.blocked_at = now
            self.toast_message("BLOCKED! 前方有箭头")

    def _complete_level(self) -> None:
        index = self.state.level_index
        self.unlocked = max(self.unlocked, min(len(LEVELS), index + 2))
        key = str(index)
        self.best_scores[key] = max(self.best_scores.get(key, 0), self.state.score)
        self._save_progress()

    def toast_message(self, message: str) -> None:
        self.toast = message
        self.toast_at = pygame.time.get_ticks()

    def game_buttons(self) -> list[Button]:
        return [
            Button(pygame.Rect(682, 480, 250, 48), "↻ 重新开始", CORAL),
            Button(pygame.Rect(682, 542, 118, 48), "↶ 撤销", LAVENDER, bool(self.state.history)),
            Button(pygame.Rect(814, 542, 118, 48), "✦ 提示", CYAN),
            Button(pygame.Rect(682, 604, 250, 48), "关卡选择", INK),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.scene = "start" if self.scene != "start" else self.scene
            elif event.key == pygame.K_r and self.scene == "game":
                self.state.restart()
                self.started_at = pygame.time.get_ticks()
            elif event.key == pygame.K_z and self.scene == "game":
                self.state.undo()
            elif event.key == pygame.K_h and self.scene == "game":
                hint = self.state.hint()
                if hint:
                    self.hint_pos = (hint.row, hint.col)
                    self.hint_at = pygame.time.get_ticks()
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        if self.scene == "start":
            if Button(pygame.Rect(350, 480, 300, 64), "开始游戏", CYAN).hit(pos):
                self.scene = "levels"
        elif self.scene == "levels":
            for index, button in enumerate(self.level_buttons()):
                if button.hit(pos):
                    self.start_level(index)
            if Button(pygame.Rect(40, 680, 130, 44), "← 返回", INK).hit(pos):
                self.scene = "start"
        elif self.scene == "game":
            if self.state.status is GameStatus.PLAYING:
                self.handle_game_click(pos)
            else:
                self.handle_result_click(pos)

    def handle_result_click(self, pos: tuple[int, int]) -> None:
        if Button(pygame.Rect(365, 475, 270, 56), "下一关", CYAN).hit(pos) and self.state.status is GameStatus.CLEARED:
            if self.state.level_index + 1 < len(LEVELS):
                self.start_level(self.state.level_index + 1)
            else:
                self.scene = "levels"
        elif Button(pygame.Rect(365, 545, 270, 52), "再试一次", CORAL).hit(pos):
            self.start_level(self.state.level_index)
        elif Button(pygame.Rect(365, 611, 270, 48), "返回关卡", INK).hit(pos):
            self.scene = "levels"

    def update(self, dt: float) -> None:
        speed = 720
        alive: list[FlyingArrow] = []
        for item in self.flying:
            dr, dc = item.arrow.direction.delta
            item.x += dc * speed * dt
            item.y += dr * speed * dt
            item.life -= dt
            if item.life > 0:
                alive.append(item)
        self.flying = alive

    def draw_text(self, text: str, key: str, color: tuple[int, int, int], position, anchor="topleft") -> pygame.Rect:
        rendered = self.fonts[key].render(text, True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, position)
        self.surface.blit(rendered, rect)
        return rect

    def draw_start(self) -> None:
        ticks = pygame.time.get_ticks()
        draw_background(self.surface, ticks)
        self.draw_text("ONE", "small", CYAN, (500, 155), "center")
        self.draw_text("一箭又一箭", "hero", INK, (500, 250), "center")
        self.draw_text("观察 · 推理 · 让每支箭找到出口", "h2", MUTED, (500, 325), "center")
        for index, direction in enumerate(self.state.arrows.values()):
            if index >= 4:
                break
            draw_arrow(self.surface, (365 + index * 90, 405), direction.direction, 28, (CYAN, CORAL, GOLD, LAVENDER)[index])
        button = Button(pygame.Rect(350, 480, 300, 64), "开始游戏", CYAN)
        button.draw(self.surface, self.fonts["h2"], pygame.mouse.get_pos())
        self.draw_text("鼠标点击箭头 · H 提示 · Z 撤销 · R 重开", "small", MUTED, (500, 585), "center")
        self.draw_text("原创矢量界面 / 5 个可验证关卡 / AI 自动求解", "small", MUTED, (500, 704), "center")

    def level_buttons(self) -> list[Button]:
        buttons = []
        for index, level in enumerate(LEVELS):
            x = 130 + (index % 3) * 260
            y = 230 + (index // 3) * 170
            unlocked = index < self.unlocked
            label = f"{index + 1:02d}  {level.name}" if unlocked else f"🔒  {index + 1:02d}"
            buttons.append(Button(pygame.Rect(x, y, 220, 112), label, (CYAN, CORAL, GOLD, LAVENDER, INK)[index], unlocked))
        return buttons

    def draw_levels(self) -> None:
        draw_background(self.surface, pygame.time.get_ticks())
        self.draw_text("选择关卡", "title", INK, (500, 75), "center")
        self.draw_text(f"已解锁 {self.unlocked} / {len(LEVELS)}", "body", MUTED, (500, 115), "center")
        for index, button in enumerate(self.level_buttons()):
            button.draw(self.surface, self.fonts["body"], pygame.mouse.get_pos())
            if button.enabled:
                best = self.best_scores.get(str(index))
                detail = f"最佳 {best}" if best else f"{sum(v is not None for row in LEVELS[index].layout for v in row)} 支箭"
                self.draw_text(detail, "small", MUTED, (button.rect.centerx, button.rect.bottom - 20), "center")
        back = Button(pygame.Rect(40, 680, 130, 44), "← 返回", INK)
        back.draw(self.surface, self.fonts["body"], pygame.mouse.get_pos())

    def draw_game(self) -> None:
        now = pygame.time.get_ticks()
        draw_background(self.surface, now)
        self.draw_text(f"LEVEL {self.state.level_index + 1:02d}", "small", CYAN, (56, 48))
        self.draw_text(self.state.level.name, "title", INK, (56, 70))
        board, cell = self.board_geometry()
        pygame.draw.rect(self.surface, (211, 207, 197), board.move(0, 6), border_radius=24)
        pygame.draw.rect(self.surface, PANEL, board, border_radius=24)
        for i in range(1, self.state.level.size):
            x = board.left + i * cell
            y = board.top + i * cell
            pygame.draw.line(self.surface, (226, 222, 212), (x, board.top + 18), (x, board.bottom - 18))
            pygame.draw.line(self.surface, (226, 222, 212), (board.left + 18, y), (board.right - 18, y))

        palette = {"UP": CYAN, "DOWN": CORAL, "LEFT": GOLD, "RIGHT": LAVENDER}
        for arrow in self.state.arrows.values():
            center = list(self.cell_center(arrow.row, arrow.col))
            color = palette[arrow.direction.value]
            rotation = 0.0
            if self.blocked_pos == (arrow.row, arrow.col) and now - self.blocked_at < 650:
                center[0] += 7 * (1 if (now // 55) % 2 else -1)
                color = CORAL
                rotation = 5 * (1 if (now // 70) % 2 else -1)
            if self.hint_pos == (arrow.row, arrow.col) and now - self.hint_at < 2400:
                pulse = 4 + (now // 120) % 4
                pygame.draw.circle(self.surface, CYAN, (round(center[0]), round(center[1])), int(cell * .37) + pulse, 3)
            draw_arrow(self.surface, center, arrow.direction, min(cell * .34, 30), color, rotation=rotation)

        for item in self.flying:
            alpha = max(0, min(255, int(item.life / .48 * 255)))
            draw_arrow(self.surface, (item.x, item.y), item.arrow.direction, min(cell * .34, 30), CYAN, alpha)

        self.draw_sidebar()
        if self.toast and now - self.toast_at < 1600:
            toast_rect = pygame.Rect(250, 672, 380, 44)
            pygame.draw.rect(self.surface, INK, toast_rect, border_radius=16)
            self.draw_text(self.toast, "body", PANEL, toast_rect.center, "center")
        if self.state.status is not GameStatus.PLAYING:
            self.draw_result_overlay()

    def draw_sidebar(self) -> None:
        x = 682
        self.draw_text("本局状态", "h2", INK, (x, 144))
        cards = [
            ("剩余箭头", str(self.state.remaining), CYAN),
            ("失误机会", "● " * self.state.mistakes + "○ " * (self.state.max_mistakes - self.state.mistakes), CORAL),
            ("当前得分", str(self.state.score), GOLD),
            ("用时", f"{self.elapsed():02d}s", LAVENDER),
        ]
        for index, (label, value, color) in enumerate(cards):
            rect = pygame.Rect(x, 188 + index * 67, 250, 54)
            pygame.draw.rect(self.surface, PANEL, rect, border_radius=14)
            pygame.draw.rect(self.surface, color, pygame.Rect(rect.x, rect.y, 6, rect.h), border_radius=3)
            self.draw_text(label, "small", MUTED, (rect.x + 18, rect.y + 9))
            self.draw_text(value, "body", INK, (rect.right - 16, rect.centery), "midright")
        for button in self.game_buttons():
            button.draw(self.surface, self.fonts["body"], pygame.mouse.get_pos())
        self.draw_text("快捷键  H 提示  Z 撤销  R 重开", "small", MUTED, (807, 685), "center")

    def draw_result_overlay(self) -> None:
        shade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        shade.fill((29, 35, 58, 178))
        self.surface.blit(shade, (0, 0))
        card = pygame.Rect(285, 125, 430, 555)
        pygame.draw.rect(self.surface, PANEL, card, border_radius=28)
        cleared = self.state.status is GameStatus.CLEARED
        color = CYAN if cleared else CORAL
        self.draw_text("关卡完成!" if cleared else "挑战失败", "title", color, (500, 185), "center")
        subtitle = "每支箭都找到了自己的出口" if cleared else "别急，重新观察箭头的阻挡关系"
        self.draw_text(subtitle, "body", MUTED, (500, 235), "center")
        if cleared:
            stars = self.stars()
            self.draw_text("★" * stars + "☆" * (3 - stars), "hero", GOLD, (500, 320), "center")
            self.draw_text(f"得分 {self.state.score}   ·   用时 {self.elapsed()} 秒", "body", INK, (500, 395), "center")
            next_button = Button(pygame.Rect(365, 475, 270, 56), "下一关", CYAN)
            next_button.draw(self.surface, self.fonts["h2"], pygame.mouse.get_pos())
        else:
            self.draw_text("×", "hero", CORAL, (500, 330), "center")
            self.draw_text("失误机会已耗尽", "h2", INK, (500, 395), "center")
        retry = Button(pygame.Rect(365, 545, 270, 52), "再试一次", CORAL)
        back = Button(pygame.Rect(365, 611, 270, 48), "返回关卡", INK)
        retry.draw(self.surface, self.fonts["body"], pygame.mouse.get_pos())
        back.draw(self.surface, self.fonts["body"], pygame.mouse.get_pos())

    def draw(self) -> None:
        if self.scene == "start":
            self.draw_start()
        elif self.scene == "levels":
            self.draw_levels()
        else:
            self.draw_game()
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()

    def capture(self, output_dir: Path) -> None:
        """Create deterministic README screenshots without manual interaction."""
        output_dir.mkdir(parents=True, exist_ok=True)
        self.scene = "start"
        self.draw()
        pygame.image.save(self.surface, output_dir / "01_start.png")
        self.unlocked = len(LEVELS)
        self.scene = "levels"
        self.draw()
        pygame.image.save(self.surface, output_dir / "02_levels.png")
        self.start_level(2)
        self.draw()
        pygame.image.save(self.surface, output_dir / "03_game.png")
        while self.state.status is GameStatus.PLAYING:
            hint = self.state.hint()
            if hint is None:
                break
            self.state.click(hint.row, hint.col)
        self.draw()
        pygame.image.save(self.surface, output_dir / "04_clear.png")
        self.start_level(1)
        blocked = next(a for a in self.state.arrows.values() if not self.state.can_exit(a.row, a.col))
        for _ in range(self.state.max_mistakes):
            self.state.click(blocked.row, blocked.col)
        self.draw()
        pygame.image.save(self.surface, output_dir / "05_failed.png")
        pygame.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One Arrow Game")
    parser.add_argument("--capture", type=Path, help="save UI screenshots and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.capture:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    app = GameApp(headless=bool(args.capture))
    if args.capture:
        app.capture(args.capture)
    else:
        app.run()


if __name__ == "__main__":
    main()


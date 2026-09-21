"""Generate a readable five-level manual-playtest style GIF."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

from game_state import solve
from level import LEVELS
from main import BASE_DIR, FlyingArrow, GameApp
from ui import CORAL, CYAN, INK, MUTED, PANEL, draw_background


OUTPUT = BASE_DIR / "assets" / "screenshots" / "gameplay_demo.gif"
GIF_SIZE = (600, 456)


def frame(
    app: GameApp,
    target: tuple[int, int] | None = None,
    step: tuple[int, int] | None = None,
) -> Image.Image:
    app.draw()
    if target is not None:
        # A short "thinking" frame before every move makes the recording read
        # like a person inspecting and clicking the board, not an instant bot.
        x, y = app.cell_center(*target)
        pygame.draw.circle(app.surface, PANEL, (round(x), round(y)), 25, 5)
        pygame.draw.circle(app.surface, CYAN, (round(x), round(y)), 32, 4)
        pygame.draw.circle(app.surface, INK, (round(x), round(y)), 6)
    if step is not None:
        current, total = step
        label = f"通关演示  ·  第 {app.state.level_index + 1}/5 关  ·  第 {current}/{total} 步"
        banner = pygame.Rect(210, 25, 580, 42)
        pygame.draw.rect(app.surface, PANEL, banner, border_radius=16)
        pygame.draw.rect(app.surface, CYAN, banner, 3, border_radius=16)
        app.draw_text(label, "small", INK, banner.center, "center")
    raw = pygame.image.tostring(app.surface, "RGB")
    image = Image.frombytes("RGB", app.surface.get_size(), raw)
    image = image.resize(GIF_SIZE, Image.Resampling.LANCZOS)
    return image.quantize(colors=96, method=Image.Quantize.MEDIANCUT)


def title_card(app: GameApp, level_index: int, arrow_count: int) -> Image.Image:
    """Insert an unmistakable divider so all five tested levels are visible."""
    draw_background(app.surface, 0)
    app.draw_text("五关通关演示", "small", CYAN, (500, 205), "center")
    app.draw_text(f"第 {level_index + 1} / {len(LEVELS)} 关", "hero", INK, (500, 300), "center")
    app.draw_text(LEVELS[level_index].name, "title", CORAL, (500, 375), "center")
    app.draw_text(f"本关共 {arrow_count} 支箭  ·  全程无提示、无失误", "body", MUTED, (500, 440), "center")
    app.draw_text("观察路径后再点击安全箭头", "small", MUTED, (500, 505), "center")
    pygame.display.flip()
    raw = pygame.image.tostring(app.surface, "RGB")
    image = Image.frombytes("RGB", app.surface.get_size(), raw)
    image = image.resize(GIF_SIZE, Image.Resampling.LANCZOS)
    return image.quantize(colors=96, method=Image.Quantize.MEDIANCUT)


def main() -> None:
    app = GameApp(headless=True)
    app.unlocked = len(LEVELS)
    frames: list[Image.Image] = []
    durations: list[int] = []

    for level_index in range(len(LEVELS)):
        app.start_level(level_index)
        solution = solve(app.state.arrows.values(), app.state.level.size)
        if solution is None:
            raise RuntimeError(f"Level {level_index + 1} is not solvable")

        frames.append(title_card(app, level_index, len(solution)))
        durations.append(1500)

        opening = frame(app)
        frames.append(opening)
        durations.append(900)

        for move_index, (row, col) in enumerate(solution, start=1):
            # Pause on the intended arrow before clicking it.
            frames.append(frame(app, (row, col), (move_index, len(solution))))
            durations.append(380 + (move_index % 3) * 70)

            result = app.state.click(row, col)
            if result.arrow is None:
                raise RuntimeError("Solver produced an invalid move")
            x, y = app.cell_center(row, col)
            app.flying.append(FlyingArrow(result.arrow, x, y))
            app.update(0.12)
            frames.append(frame(app, step=(move_index, len(solution))))
            durations.append(130)
            app.update(0.18)
            frames.append(frame(app, step=(move_index, len(solution))))
            durations.append(260)

        frames.append(frame(app))
        durations.append(1900)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    pygame.quit()
    print(f"Generated {OUTPUT} ({len(frames)} frames)")


if __name__ == "__main__":
    main()

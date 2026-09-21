"""Generate a compact five-level gameplay GIF for the project report."""

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


OUTPUT = BASE_DIR / "assets" / "screenshots" / "gameplay_demo.gif"
GIF_SIZE = (600, 456)


def frame(app: GameApp) -> Image.Image:
    app.draw()
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

        opening = frame(app)
        frames.append(opening)
        durations.append(650)

        for row, col in solution:
            result = app.state.click(row, col)
            if result.arrow is None:
                raise RuntimeError("Solver produced an invalid move")
            x, y = app.cell_center(row, col)
            app.flying.append(FlyingArrow(result.arrow, x, y))
            app.update(0.13)
            frames.append(frame(app))
            durations.append(125)

        frames.append(frame(app))
        durations.append(850)

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

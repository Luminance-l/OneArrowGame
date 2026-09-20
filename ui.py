"""Small reusable Pygame widgets and drawing helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from constants import Direction


INK = (29, 35, 58)
MUTED = (102, 111, 138)
PAPER = (247, 244, 236)
PANEL = (255, 253, 247)
CYAN = (35, 193, 190)
CORAL = (245, 101, 101)
GOLD = (247, 185, 65)
LAVENDER = (118, 105, 190)


@dataclass(slots=True)
class Button:
    rect: pygame.Rect
    label: str
    accent: tuple[int, int, int] = INK
    enabled: bool = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse: tuple[int, int]) -> None:
        hovered = self.enabled and self.rect.collidepoint(mouse)
        color = self.accent if self.enabled else (190, 190, 190)
        fill = color if hovered else PANEL
        text_color = PANEL if hovered else color
        pygame.draw.rect(surface, (215, 210, 199), self.rect.move(0, 4), border_radius=14)
        pygame.draw.rect(surface, fill, self.rect, border_radius=14)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=14)
        rendered = font.render(self.label, True, text_color)
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def hit(self, position: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(position)


def draw_arrow(
    surface: pygame.Surface,
    center: tuple[float, float],
    direction: Direction,
    size: float,
    color: tuple[int, int, int],
    alpha: int = 255,
    rotation: float = 0,
) -> None:
    """Draw a crisp vector arrow without external copyrighted assets."""
    layer = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
    cx = cy = size
    points = [
        (cx - size * .42, cy - size * .13),
        (cx + size * .08, cy - size * .13),
        (cx + size * .08, cy - size * .36),
        (cx + size * .48, cy),
        (cx + size * .08, cy + size * .36),
        (cx + size * .08, cy + size * .13),
        (cx - size * .42, cy + size * .13),
    ]
    rgba = (*color, alpha)
    pygame.draw.polygon(layer, rgba, points)
    pygame.draw.polygon(layer, (*INK, alpha), points, max(1, int(size * .06)))
    angle = {
        Direction.RIGHT: 0,
        Direction.DOWN: -90,
        Direction.LEFT: 180,
        Direction.UP: 90,
    }[direction] + rotation
    layer = pygame.transform.rotozoom(layer, angle, 1)
    surface.blit(layer, layer.get_rect(center=(round(center[0]), round(center[1]))))


def draw_background(surface: pygame.Surface, ticks: int) -> None:
    surface.fill(PAPER)
    for x in range(-50, surface.get_width() + 80, 90):
        offset = int(8 * math.sin(ticks / 900 + x))
        pygame.draw.circle(surface, (232, 228, 217), (x + offset, 75), 3)
    pygame.draw.circle(surface, (225, 241, 236), (910, 80), 120)
    pygame.draw.circle(surface, (241, 224, 218), (70, 700), 150)


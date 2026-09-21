"""Resilient audio playback for music and game feedback."""

from __future__ import annotations

from pathlib import Path

import pygame


class AudioManager:
    """Load and play the original WAV assets without making audio mandatory."""

    def __init__(self, asset_dir: Path):
        self.asset_dir = asset_dir
        self.available = False
        self.muted = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22_050, size=-16, channels=2, buffer=512)
            self.sounds = {
                name: pygame.mixer.Sound(asset_dir / f"{name}.wav")
                for name in ("launch", "wrong", "failure", "clear", "button")
            }
            volumes = {
                "launch": 0.35,
                "wrong": 0.55,
                "failure": 0.58,
                "clear": 0.58,
                "button": 0.26,
            }
            for name, sound in self.sounds.items():
                sound.set_volume(volumes[name])
            pygame.mixer.music.load(asset_dir / "background.wav")
            pygame.mixer.music.set_volume(0.24)
            pygame.mixer.music.play(-1, fade_ms=1200)
            self.available = True
        except (pygame.error, FileNotFoundError, OSError):
            # Audio must never prevent the puzzle from starting.
            self.available = False

    def play(self, name: str) -> None:
        if self.available and not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle(self) -> bool:
        if not self.available:
            return False
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.music.pause()
            pygame.mixer.stop()
        else:
            pygame.mixer.music.unpause()
            self.play("button")
        return not self.muted

    @property
    def label(self) -> str:
        if not self.available:
            return "声音：不可用"
        return "声音：关" if self.muted else "声音：开"


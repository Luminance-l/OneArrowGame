"""Generate the project's original music and effects using only the stdlib.

Run from the project root with: python tools/generate_audio.py
"""

from __future__ import annotations

import math
import random
import wave
from array import array
from pathlib import Path


RATE = 22_050
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "audio"
TAU = math.tau


def midi(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def envelope(t: float, duration: float, attack: float = .03, release: float = .24) -> float:
    return min(1.0, t / attack) * min(1.0, max(0.0, duration - t) / release)


def tone(freq: float, t: float, kind: str = "soft") -> float:
    if kind == "bell":
        return (
            math.sin(TAU * freq * t)
            + .34 * math.sin(TAU * freq * 2.01 * t)
            + .12 * math.sin(TAU * freq * 3.98 * t)
        ) / 1.46
    if kind == "pad":
        return (
            math.sin(TAU * freq * t)
            + .24 * math.sin(TAU * freq * .5 * t)
            + .14 * math.sin(TAU * freq * 2 * t)
        ) / 1.38
    return (math.sin(TAU * freq * t) + .18 * math.sin(TAU * freq * 2 * t)) / 1.18


def write_wav(path: Path, samples: list[float]) -> None:
    peak = max(1.0, max(abs(v) for v in samples))
    pcm = array("h", (int(max(-1, min(1, value / peak)) * 32767) for value in samples))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(RATE)
        stream.writeframes(pcm.tobytes())


def add_note(samples: list[float], start: float, duration: float, note: int, volume: float, kind: str) -> None:
    begin = int(start * RATE)
    end = min(len(samples), int((start + duration) * RATE))
    frequency = midi(note)
    for index in range(begin, end):
        t = (index - begin) / RATE
        samples[index] += volume * envelope(t, duration) * tone(frequency, t, kind)


def make_background() -> None:
    # Eight-bar, seamless 84 BPM progression: Cmaj7, Am7, Fmaj7, G6.
    beat = 60 / 84
    bars = 8
    duration = bars * 4 * beat
    samples = [0.0] * int(duration * RATE)
    chords = [
        (48, 52, 55, 59), (45, 48, 52, 55),
        (41, 45, 48, 52), (43, 47, 50, 52),
    ] * 2
    melody = [64, 67, 71, 67, 64, 69, 67, 64, 65, 69, 72, 69, 67, 71, 69, 62]
    for bar, chord in enumerate(chords):
        start = bar * 4 * beat
        for note in chord:
            add_note(samples, start, 4 * beat, note, .075, "pad")
        # A gentle broken-chord pulse keeps the loop moving.
        pattern = (chord[0] + 12, chord[2] + 12, chord[1] + 12, chord[3] + 12)
        for step, note in enumerate(pattern):
            add_note(samples, start + step * beat, beat * .78, note, .105, "soft")
        for half in range(2):
            note = melody[bar * 2 + half]
            add_note(samples, start + (half * 2 + .25) * beat, beat * 1.35, note, .10, "bell")
    # Short crossfade makes the music loop without a click.
    fade = int(.45 * RATE)
    for i in range(fade):
        ratio = i / fade
        samples[i] = samples[i] * ratio + samples[-fade + i] * (1 - ratio)
        samples[-fade + i] *= 1 - ratio
    write_wav(OUTPUT / "background.wav", samples)


def make_effect(name: str, duration: float, builder) -> None:
    samples = [builder(i / RATE, duration) for i in range(int(duration * RATE))]
    write_wav(OUTPUT / f"{name}.wav", samples)


def main() -> None:
    random.seed(7)
    make_background()
    make_effect("launch", .34, lambda t, d: .42 * envelope(t, d, .01, .18) * tone(520 + 900 * t / d, t, "soft"))
    make_effect("button", .12, lambda t, d: .28 * envelope(t, d, .005, .07) * tone(660, t, "bell"))
    make_effect(
        "wrong", .42,
        lambda t, d: .44 * envelope(t, d, .01, .20) * tone(220 - 55 * t / d, t, "soft"),
    )
    make_effect(
        "failure", 1.05,
        lambda t, d: .45 * envelope(t, d, .02, .35) * (
            tone(196 - 45 * t / d, t, "pad") + .45 * tone(147 - 32 * t / d, t, "soft")
        ),
    )

    clear_notes = (60, 64, 67, 72)
    clear = [0.0] * int(1.45 * RATE)
    for index, note in enumerate(clear_notes):
        add_note(clear, index * .19, .78, note, .28, "bell")
    write_wav(OUTPUT / "clear.wav", clear)
    print(f"Generated original audio in {OUTPUT}")


if __name__ == "__main__":
    main()


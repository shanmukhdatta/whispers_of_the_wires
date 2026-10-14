"""Deterministic CPU-only multitrack composer and MIDI validation baseline."""
from __future__ import annotations

import random
from pathlib import Path

import pretty_midi

from wow.contracts import MusicBlueprint

ROOTS = {"C_major": 60, "G_major": 67, "F_major": 65, "A_minor": 57}
SCALES = {
    "C_major": [0, 2, 4, 5, 7, 9, 11],
    "G_major": [0, 2, 4, 5, 7, 9, 11],
    "F_major": [0, 2, 4, 5, 7, 9, 11],
    "A_minor": [0, 2, 3, 5, 7, 8, 10],
}


def _add(inst: pretty_midi.Instrument, pitch: int, start: float,
         end: float, velocity: int) -> None:
    if end <= start:
        raise ValueError("Invalid note duration")
    inst.notes.append(pretty_midi.Note(
        velocity=max(1, min(127, velocity)),
        pitch=max(0, min(127, pitch)),
        start=start,
        end=end,
    ))


def compose_rule_based(blueprint: MusicBlueprint) -> pretty_midi.PrettyMIDI:
    """Four-role arrangement; transparent baseline, NOT the pretrained AI model."""
    rng = random.Random(blueprint.generation.seed)
    midi = pretty_midi.PrettyMIDI(initial_tempo=blueprint.tempo_bpm)
    instruments = {
        t.id: pretty_midi.Instrument(program=t.program, is_drum=t.is_drum, name=t.id)
        for t in blueprint.tracks
    }
    beat = 60 / blueprint.tempo_bpm
    bar_duration = beat * 4
    root = ROOTS[blueprint.key]
    scale = SCALES[blueprint.key]
    chord_steps = [0, 3, 4, 0]
    for bar in range(blueprint.total_bars):
        sec = next(s for s in blueprint.sections
                   if s.start_bar <= bar < s.start_bar + s.bar_count)
        energy = (sec.arousal + 1) / 2
        velocity = int(46 + 52 * energy)
        start = bar * bar_duration
        degree = chord_steps[bar % len(chord_steps)]
        chord_root = root + scale[degree] - 12
        third = root + scale[(degree + 2) % 7] - 12
        fifth = root + scale[(degree + 4) % 7] - 12
        if "harmony" in instruments:
            for pitch in (chord_root, third, fifth):
                _add(instruments["harmony"], pitch, start, start + bar_duration * 0.95,
                     max(20, velocity - 18))
        if "bass" in instruments:
            _add(instruments["bass"], chord_root - 12, start,
                 start + bar_duration * 0.8, max(20, velocity - 8))
        if "melody" in instruments:
            count = 4 if energy >= 0.65 else 2
            step = bar_duration / count
            for n in range(count):
                pitch = root + scale[(degree + n + rng.choice([-1, 0, 1])) % 7]
                _add(instruments["melody"], pitch + 12, start + n * step,
                     start + (n + 0.82) * step, velocity)
        if "drums" in instruments:
            for n in range(4):
                if n in (0, 2):
                    _add(instruments["drums"], 36, start + n * beat,
                         start + n * beat + 0.08, velocity)
                if n in (1, 3) and energy >= 0.45:
                    _add(instruments["drums"], 38, start + n * beat,
                         start + n * beat + 0.08, velocity - 10)
    midi.instruments = list(instruments.values())
    return midi


def save_midi(midi: pretty_midi.PrettyMIDI, destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    midi.write(str(destination))
    return destination


def validate_midi(path: Path, expected_tracks: int | None = None) -> dict:
    midi = pretty_midi.PrettyMIDI(str(path))
    notes = sum(len(t.notes) for t in midi.instruments)
    if notes == 0:
        raise ValueError("MIDI contains no notes")
    if expected_tracks is not None and len(midi.instruments) != expected_tracks:
        raise ValueError("Unexpected number of MIDI tracks")
    if any(note.end <= note.start for t in midi.instruments for note in t.notes):
        raise ValueError("MIDI contains invalid note times")
    return {"track_count": len(midi.instruments),
            "note_count": notes, "duration_seconds": midi.get_end_time()}

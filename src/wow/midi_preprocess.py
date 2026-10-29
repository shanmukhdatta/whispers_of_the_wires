"""Safe, reproducible symbolic preprocessing for authorized training data."""
from __future__ import annotations

import copy
from pathlib import Path

import pretty_midi


def quantize_midi(
    original: Path, destination: Path, *, subdivisions_per_beat: int = 4,
) -> dict:
    """Write a new normalized-timing MIDI without overwriting the input."""
    if subdivisions_per_beat not in {1, 2, 4, 8}:
        raise ValueError("Supported beat subdivisions: 1, 2, 4, or 8")
    source = Path(original).resolve()
    destination = Path(destination).resolve()
    if source == destination:
        raise ValueError("Never overwrite original training data")
    midi = pretty_midi.PrettyMIDI(str(source))
    tempo = float(midi.get_tempo_changes()[1][0])
    step = 60.0 / (tempo * subdivisions_per_beat)
    processed = copy.deepcopy(midi)
    moved = 0
    for instrument in processed.instruments:
        for note in instrument.notes:
            previous = (note.start, note.end)
            start = round(note.start / step) * step
            end = max(start + step, round(note.end / step) * step)
            note.start = max(0.0, start)
            note.end = end
            moved += int(previous != (note.start, note.end))
    destination.parent.mkdir(parents=True, exist_ok=True)
    processed.write(str(destination))
    return {
        "source": source.name, "output": destination.name,
        "tempo_bpm": round(tempo, 4),
        "grid_seconds": round(step, 8), "notes_adjusted": moved,
    }

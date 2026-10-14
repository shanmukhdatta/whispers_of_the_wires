"""Dependable CPU WAV preview renderer; intentionally simple, not a neural synthesizer."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf


def render_wav(midi_path: Path, wav_path: Path, *, sample_rate: int = 22050) -> Path:
    if sample_rate not in (22050, 44100):
        raise ValueError("Unsupported sample rate")
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    duration = midi.get_end_time() + 0.2
    if duration <= 0.2 or duration > 240:
        raise ValueError("Invalid or overly long MIDI for preview rendering")
    data = np.zeros(int(duration * sample_rate), dtype=np.float32)
    for instrument in midi.instruments:
        for note in instrument.notes:
            start = max(0, int(note.start * sample_rate))
            end = min(len(data), int(note.end * sample_rate))
            size = end - start
            if size <= 0:
                continue
            t = np.arange(size, dtype=np.float32) / sample_rate
            frequency = 440.0 * 2 ** ((note.pitch - 69) / 12)
            # Percussion deliberately sounds synthetic; do not claim realistic drums.
            if instrument.is_drum:
                tone = np.sin(2 * np.pi * (65 + (note.pitch % 7) * 19) * t)
            else:
                tone = (np.sin(2 * np.pi * frequency * t)
                        + 0.2 * np.sin(4 * np.pi * frequency * t))
            attack = np.minimum(1.0, t / 0.015)
            release = np.minimum(1.0, (size - np.arange(size)) / (0.06 * sample_rate))
            envelope = np.maximum(0, np.minimum(attack, release))
            data[start:end] += 0.13 * (note.velocity / 127) * tone * envelope
    peak = float(np.max(np.abs(data)))
    if peak > 0:
        data *= min(1.0, 0.90 / peak)
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(wav_path), data, sample_rate, subtype="PCM_16")
    return wav_path

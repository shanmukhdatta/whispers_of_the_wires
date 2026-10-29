"""Reproducible feature extraction for owned/authorized MIDI and WAV files."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf


def inspect_midi(source: Path) -> dict:
    midi = pretty_midi.PrettyMIDI(str(source))
    instruments = []
    for instrument in midi.instruments:
        notes = instrument.notes
        instruments.append({
            "name": instrument.name, "program": instrument.program,
            "drum": instrument.is_drum, "notes": len(notes),
            "mean_pitch": round(float(np.mean([n.pitch for n in notes])), 3)
            if notes else None,
        })
    return {
        "file": Path(source).name, "kind": "midi",
        "duration_seconds": round(midi.get_end_time(), 4),
        "tracks": len(instruments), "instruments": instruments,
        "valid": bool(instruments and sum(t["notes"] for t in instruments) > 0),
    }


def inspect_audio(source: Path) -> dict:
    info = sf.info(str(source))
    if info.duration > 3600:
        raise ValueError("Audio longer than one hour is outside pipeline scope")
    audio, sr = sf.read(str(source), always_2d=True, dtype="float32")
    if not sr or not len(audio):
        raise ValueError("Empty audio")
    return {
        "file": Path(source).name, "kind": "audio",
        "duration_seconds": round(len(audio) / sr, 4),
        "sample_rate": sr, "channels": audio.shape[1],
        "peak": round(float(np.max(np.abs(audio))), 6),
        "rms": round(float(np.sqrt(np.mean(audio ** 2))), 6),
        "silent": bool(np.max(np.abs(audio)) < 1e-5),
        "clipping": bool(np.any(np.abs(audio) >= 0.999)),
    }


def inspect_dataset(folder: Path, max_files: int = 100) -> dict:
    if not 1 <= max_files <= 10000:
        raise ValueError("max_files outside 1..10000")
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Dataset directory does not exist")
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and not p.is_symlink() and
                   p.suffix.lower() in {".mid", ".midi", ".wav", ".flac"})
    results = []
    for source in files[:max_files]:
        try:
            item = (inspect_midi(source) if source.suffix.lower() in {".mid", ".midi"}
                    else inspect_audio(source))
            results.append(item)
        except (ValueError, OSError, EOFError) as exc:
            results.append({
                "file": source.name, "valid": False, "error": type(exc).__name__
            })
    return {"scanned": len(results), "total_detected": len(files),
            "results": results}

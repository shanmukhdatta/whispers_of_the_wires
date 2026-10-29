"""Bounded, non-destructive listening previews and crossfaded local playlists."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt


def _load(path: Path) -> tuple[np.ndarray, int]:
    info = sf.info(str(path))
    if info.duration <= 0 or info.duration > 240:
        raise ValueError("Invalid audio duration for local preview")
    signal, sr = sf.read(str(path), dtype="float32", always_2d=True)
    if not 0 < sr <= 96000 or not len(signal):
        raise ValueError("Unsupported audio sample rate or empty track")
    return signal, sr


def audio_bytes(signal: np.ndarray, rate: int) -> bytes:
    if signal.size == 0:
        raise ValueError("Cannot export empty music")
    dest = io.BytesIO()
    sf.write(dest, np.clip(signal, -0.98, 0.98), rate, format="WAV", subtype="PCM_16")
    return dest.getvalue()


def transform_preview(
    path: Path, *, gain: float = 1.0, lowpass_hz: int | None = None,
) -> bytes:
    """Volume + optional 4th-order lowpass; original file remains untouched."""
    if not 0.0 <= gain <= 2.0:
        raise ValueError("Gain outside 0..2")
    samples, rate = _load(path)
    if lowpass_hz is not None:
        if not 80 <= lowpass_hz < rate // 2:
            raise ValueError("Filter cutoff outside valid audio range")
        filt = butter(4, lowpass_hz, btype="lowpass", fs=rate, output="sos")
        samples = sosfilt(filt, samples, axis=0).astype("float32")
    return audio_bytes(samples * gain, rate)


def crossfade_playlist(
    wav_files: list[Path], *, fade_seconds: float = 1.5,
    gain: float = 1.0, max_seconds: float = 240.0,
) -> bytes:
    """Render up to 8 owned recordings into one WAV with overlap equal-power fades."""
    if not 1 <= len(wav_files) <= 8:
        raise ValueError("Select one to eight existing tracks")
    if not 0 <= fade_seconds <= 8:
        raise ValueError("Crossfade must be 0..8 seconds")
    if not 0 <= gain <= 2:
        raise ValueError("Gain must be 0..2")
    combined = None
    sample_rate = None
    for path in wav_files:
        signal, sr = _load(path)
        signal = signal.mean(axis=1).astype("float32")
        if sample_rate is None:
            sample_rate = sr
        if sr != sample_rate:
            raise ValueError("Tracks must use the same sample rate")
        if combined is None:
            combined = signal
        else:
            n = min(int(fade_seconds * sr), len(combined), len(signal))
            if n:
                phase = np.linspace(0, np.pi / 2, n, dtype="float32")
                overlapping = (
                    combined[-n:] * np.cos(phase) + signal[:n] * np.sin(phase)
                )
                combined = np.concatenate(
                    [combined[:-n], overlapping, signal[n:]]
                )
            else:
                combined = np.concatenate([combined, signal])
        if len(combined) / sr > max_seconds:
            raise ValueError("Playlist exceeds four-minute offline listening limit")
    assert combined is not None and sample_rate is not None
    return audio_bytes(combined * gain, sample_rate)

"""Audio/MIDI descriptors from the implementation guide, computed without learned claims."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf
from scipy.fft import dct
from scipy.signal import stft


def _hz_to_mel(hz: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _mel_filters(frequencies: np.ndarray, bands: int = 26) -> np.ndarray:
    maximum = _hz_to_mel(np.asarray([frequencies[-1]], dtype=float))[0]
    centers = _mel_to_hz(np.linspace(0, maximum, bands + 2))
    filters = np.zeros((bands, len(frequencies)), dtype=np.float64)
    for index in range(bands):
        left, middle, right = centers[index:index + 3]
        rising = (frequencies - left) / max(middle - left, 1e-9)
        falling = (right - frequencies) / max(right - middle, 1e-9)
        filters[index] = np.maximum(0, np.minimum(rising, falling))
    return filters


def extract_music_features(midi_path: Path, wav_path: Path) -> dict:
    """One-piece interpretable features; MFCCs are a handcrafted scipy estimate."""
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    samples, rate = sf.read(str(wav_path), always_2d=True, dtype="float32")
    if len(samples) < 2048 or not rate:
        raise ValueError("At least 2048 audio samples are required")
    if len(samples) / rate > 300:
        raise ValueError("Audio exceeds 5-minute analysis limit")
    mono = samples.mean(axis=1)
    frequency, _, spectrum = stft(
        mono, fs=rate, nperseg=2048, noverlap=1536, boundary=None,
    )
    magnitude = np.abs(spectrum)
    power = magnitude ** 2
    weight = magnitude.sum(axis=0) + 1e-12
    centroids = (frequency[:, None] * magnitude).sum(axis=0) / weight
    cumsum = np.cumsum(magnitude, axis=0)
    rolloff_index = (cumsum < 0.85 * cumsum[-1]).sum(axis=0)
    rolloff = frequency[np.minimum(rolloff_index, len(frequency) - 1)]
    filters = _mel_filters(frequency)
    mel_energy = filters @ power
    cepstra = dct(np.log(np.maximum(mel_energy, 1e-12)), type=2, axis=0, norm="ortho")
    mfcc = np.mean(cepstra[:13], axis=1)
    chroma = np.zeros(12, dtype=float)
    onsets = 0
    for track in midi.instruments:
        onsets += len(track.notes)
        if not track.is_drum:
            for note in track.notes:
                chroma[note.pitch % 12] += max(0, note.end - note.start)
    chroma /= max(1e-9, chroma.sum())
    tempos = midi.get_tempo_changes()[1]
    return {
        "schema_version": "1.0",
        "audio": {
            "spectral_centroid_mean_hz": round(float(centroids.mean()), 3),
            "spectral_rolloff_85_mean_hz": round(float(rolloff.mean()), 3),
            "mfcc_mean_13": [round(float(x), 4) for x in mfcc],
            "sample_rate": rate,
        },
        "symbolic": {
            "chroma_12": [round(float(x), 6) for x in chroma],
            "note_onsets": onsets,
            "onsets_per_second": round(onsets / max(midi.get_end_time(), 1), 4),
            "midi_tempo_bpm": round(float(tempos[0]), 3) if len(tempos) else None,
        },
        "caveat": "Descriptive features only: not a CLAP/FAD score or mood validation",
    }

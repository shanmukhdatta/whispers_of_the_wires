"""Offline, opt-in MP3 export from generated WAV using system FFmpeg."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class CodecUnavailable(RuntimeError):
    """System audio encoder is not installed."""


def convert_wav_to_mp3(wav: Path, destination: Path, bitrate: str = "192k") -> Path:
    wav = Path(wav)
    destination = Path(destination)
    encoder = shutil.which("ffmpeg")
    if encoder is None:
        raise CodecUnavailable("MP3 export requires FFmpeg installed on this computer")
    if not wav.is_file():
        raise FileNotFoundError(wav)
    if bitrate not in {"128k", "192k", "256k"}:
        raise ValueError("Unsupported MP3 bitrate")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [encoder, "-nostdin", "-hide_banner", "-loglevel", "error",
             "-y", "-i", str(wav), "-codec:a", "libmp3lame",
             "-b:a", bitrate, str(destination)],
            check=True, timeout=50, capture_output=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError("MP3 encoding failed") from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("Encoder produced no MP3 file")
    return destination

"""Non-destructive filtering, volume and equal-power playlist overlap."""
import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from wow.api import app
from wow.audio_processing import crossfade_playlist, transform_preview
from wow.contracts import default_blueprint
from wow.generation import GenerationService


def test_eq_and_mix_preserve_originals(tmp_path):
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    sr = 22050
    t = np.arange(sr, dtype="float32") / sr
    sf.write(a, 0.2 * np.sin(2 * np.pi * 220 * t), sr)
    sf.write(b, 0.1 * np.sin(2 * np.pi * 330 * t), sr)
    original = a.read_bytes()
    softened = transform_preview(a, gain=0.5, lowpass_hz=900)
    audio, samplerate = sf.read(io.BytesIO(softened))
    assert samplerate == sr
    assert np.max(np.abs(audio)) < 0.2
    playlist = crossfade_playlist([a, b], fade_seconds=0.5)
    samples, _ = sf.read(io.BytesIO(playlist))
    assert 1.49 <= len(samples) / sr <= 1.51
    assert a.read_bytes() == original


def test_audio_listening_api_and_empty_playlist(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    result = GenerationService(tmp_path).create(default_blueprint("calm study music"))
    assert result["state"] == "completed"
    client = TestClient(app)
    comp = result["job_id"]
    raw = (tmp_path / "artifacts" / comp / "composition.wav").read_bytes()
    listened = client.get(
        f"/api/v1/compositions/{comp}/listen",
        params={"volume_percent": 60, "lowpass_hz": 1200},
    )
    assert listened.status_code == 200, listened.text
    assert listened.content[:4] == b"RIFF"
    assert (tmp_path / "artifacts" / comp / "composition.wav").read_bytes() == raw
    playlist = client.post("/api/v1/playlists", json={"name": "My first set"}).json()
    pid = playlist["id"]
    assert client.get(f"/api/v1/playlists/{pid}/listen").status_code == 422
    assert client.post(
        f"/api/v1/playlists/{pid}/items", json={"composition_id": comp}
    ).status_code == 200
    combined = client.get(f"/api/v1/playlists/{pid}/listen")
    assert combined.status_code == 200, combined.text
    assert combined.content[:4] == b"RIFF"

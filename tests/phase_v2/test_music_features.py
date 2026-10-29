"""PDF-reference spectral/MFCC/chroma and non-destructive MIDI preprocessing."""
import numpy as np
import pretty_midi
import pytest
from fastapi.testclient import TestClient

from wow.api import app
from wow.audio_features import extract_music_features
from wow.composer import compose_rule_based, save_midi
from wow.contracts import default_blueprint
from wow.generation import GenerationService
from wow.midi_preprocess import quantize_midi
from wow.rendering import render_wav


def test_audio_descriptors_exist_and_are_numeric(tmp_path):
    source = save_midi(
        compose_rule_based(default_blueprint("peaceful study")), tmp_path / "input.mid"
    )
    wav = render_wav(source, tmp_path / "song.wav")
    result = extract_music_features(source, wav)
    assert len(result["audio"]["mfcc_mean_13"]) == 13
    assert len(result["symbolic"]["chroma_12"]) == 12
    assert np.isfinite(result["audio"]["spectral_centroid_mean_hz"])
    assert 0 < result["audio"]["spectral_rolloff_85_mean_hz"] < 11025
    assert 0.98 <= sum(result["symbolic"]["chroma_12"]) <= 1.01


def test_midi_quantization_preserves_original(tmp_path):
    source = save_midi(
        compose_rule_based(default_blueprint("joyful")), tmp_path / "source.mid"
    )
    prior = source.read_bytes()
    output = tmp_path / "processed.mid"
    result = quantize_midi(source, output, subdivisions_per_beat=4)
    assert result["grid_seconds"] > 0
    assert source.read_bytes() == prior
    assert output.is_file()
    assert sum(len(x.notes) for x in pretty_midi.PrettyMIDI(str(output)).instruments) > 0
    with pytest.raises(ValueError, match="overwrite"):
        quantize_midi(source, source)


def test_music_feature_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    job = GenerationService(tmp_path).create(default_blueprint("study music"))
    client = TestClient(app)
    good = client.get(f"/api/v1/compositions/{job['job_id']}/features")
    assert good.status_code == 200, good.text
    bad = client.get(f"/api/v1/compositions/{job['job_id']}/features?version=999")
    assert bad.status_code == 422

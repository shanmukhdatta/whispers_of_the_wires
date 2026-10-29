"""MIDI/audio preprocessing and optional system encoder contract tests."""
import soundfile as sf
import pytest

from wow.audio_export import CodecUnavailable, convert_wav_to_mp3
from wow.composer import compose_rule_based, save_midi
from wow.contracts import default_blueprint
from wow.data_pipeline import inspect_audio, inspect_dataset, inspect_midi
from wow.rendering import render_wav


def test_dataset_pipeline(tmp_path):
    midi = save_midi(compose_rule_based(default_blueprint("story")),
                     tmp_path / "composition.mid")
    audio = render_wav(midi, tmp_path / "composition.wav")
    assert inspect_midi(midi)["valid"]
    assert inspect_audio(audio)["rms"] > 0
    assert inspect_dataset(tmp_path)["scanned"] == 2
    samples, rate = sf.read(audio)
    assert len(samples) > rate


def test_codec_not_installed_fails_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr("wow.audio_export.shutil.which", lambda _: None)
    with pytest.raises(CodecUnavailable):
        convert_wav_to_mp3(tmp_path / "a.wav", tmp_path / "b.mp3")

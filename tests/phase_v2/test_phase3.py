"""CPU render/job integration tests, cloud import rejects corrupted artifacts."""

import pretty_midi
import soundfile as sf
from fastapi.testclient import TestClient

from wow.api import app
from wow.artifacts import write_manifest
from wow.composer import compose_rule_based, save_midi
from wow.contracts import GenerationSpec, default_blueprint
from wow.generation import GenerationService
from wow.rendering import render_wav


def test_render_wav(tmp_path):
    midi = save_midi(compose_rule_based(default_blueprint("sample")), tmp_path / "sample.mid")
    output = render_wav(midi, tmp_path / "sample.wav")
    audio, sr = sf.read(output)
    assert sr == 22050
    assert len(audio) > sr * 25


def test_cpu_generation_and_persistence(tmp_path):
    service = GenerationService(tmp_path)
    bp = default_blueprint("soundtrack")
    result = service.create(bp)
    assert result["state"] == "completed"
    assert service.jobs.get(result["job_id"]) == result
    file = tmp_path / "artifacts" / result["job_id"] / "composition.mid"
    assert file.exists()
    assert len(pretty_midi.PrettyMIDI(str(file)).instruments) == 4


def test_api_job_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    result = client.post("/api/v1/jobs", json=default_blueprint("music").model_dump())
    assert result.status_code == 202
    job = result.json()
    assert job["state"] == "completed"
    assert client.get("/api/v1/jobs/" + job["job_id"]).json()["state"] == "completed"


def test_cloud_import_integrity(tmp_path):
    service = GenerationService(tmp_path)
    bp = default_blueprint("cloud")
    bp.generation = GenerationSpec(provider="midigpt", checkpoint="yellow_medium")
    job = service.create(bp)
    assert job["state"] == "awaiting_cloud"
    incoming = tmp_path / "incoming" / "myrun"
    incoming.mkdir(parents=True)
    save_midi(compose_rule_based(default_blueprint("fixture")),
              incoming / "composition.mid")
    write_manifest(incoming, request_id=bp.request_id, provider="midigpt",
                   checkpoint="yellow_medium", seed=42,
                   filenames=["composition.mid"])
    (incoming / "composition.mid").write_bytes(b"corrupted")
    try:
        service.import_kaggle(job["job_id"], "myrun")
    except ValueError as exc:
        assert "checksum" in str(exc)
    else:
        raise AssertionError("Corrupt output imported")

"""Fast CPU-only contract tests, independent of GPU and pretrained weights."""
import json

import pretty_midi
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from wow.api import app
from wow.artifacts import verify_manifest, write_manifest
from wow.composer import compose_rule_based, save_midi, validate_midi
from wow.contracts import MusicBlueprint, default_blueprint


def test_blueprint_boundaries():
    blueprint = default_blueprint("Nervous, then hopeful, then calm")
    assert blueprint.total_bars == 12
    assert blueprint.duration_seconds == pytest.approx(30.0)
    bad = blueprint.model_dump()
    bad["sections"][1]["start_bar"] = 3
    with pytest.raises(ValidationError):
        MusicBlueprint.model_validate(bad)


def test_composer_roundtrip_and_seed(tmp_path):
    bp = default_blueprint("A progressive instrumental")
    p1 = save_midi(compose_rule_based(bp), tmp_path / "a.mid")
    p2 = save_midi(compose_rule_based(bp), tmp_path / "b.mid")
    assert p1.read_bytes() == p2.read_bytes()
    metrics = validate_midi(p1, expected_tracks=4)
    assert metrics["note_count"] > 30
    assert metrics["duration_seconds"] > 25
    assert len(pretty_midi.PrettyMIDI(str(p1)).instruments) == 4


def test_api_contract():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    payload = client.post("/api/v1/blueprints",
                          json={"prompt": "A story about confidence"}).json()
    assert payload["total_bars"] == 12
    assert len(payload["sections"]) == 3
    assert client.post("/api/v1/blueprints", json={"prompt": ""}).status_code == 422


def test_artifact_integrity(tmp_path):
    (tmp_path / "sample.mid").write_bytes(b"example")
    write_manifest(tmp_path, request_id="demo-1", provider="rule_based",
                   checkpoint="v1", seed=42, filenames=["sample.mid"])
    assert verify_manifest(tmp_path)["outputs"]["sample.mid"]["bytes"] == 7
    (tmp_path / "sample.mid").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        verify_manifest(tmp_path)


def test_manifest_rejects_traversal(tmp_path):
    with pytest.raises(ValueError):
        write_manifest(tmp_path, request_id="x", provider="rule_based",
                       checkpoint="v1", seed=0, filenames=["../secret"])

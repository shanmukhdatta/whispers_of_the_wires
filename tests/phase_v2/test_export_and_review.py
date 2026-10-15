"""Integrated project export and faithful mood interpretation tests."""
import io
import json
import zipfile

from fastapi.testclient import TestClient

from wow.api import app
from wow.contracts import default_blueprint
from wow.emotion import analyze_prompt
from wow.generation import GenerationService
from wow.project_archive import build_project_archive


def test_single_mood_does_not_invent_emotional_story():
    moods = analyze_prompt("quiet peaceful evening")
    assert len(moods) == 3
    assert [m.mood for m in moods] == ["peaceful"] * 3
    unknown = analyze_prompt("ancient city with starlight")
    assert all(m.needs_review for m in unknown)


def test_project_archive_is_integrity_manifested(tmp_path):
    job = GenerationService(tmp_path).create(default_blueprint("demo"))
    bundle = build_project_archive(tmp_path, job["job_id"], 1)
    with zipfile.ZipFile(bundle) as z:
        assert set(z.namelist()) == {
            "composition.mid", "composition.wav", "blueprint.json", "project_manifest.json"
        }
        manifest = json.loads(z.read("project_manifest.json"))
        assert manifest["version"] == 1
        assert manifest["assets"]["composition.mid"]["bytes"] > 0
    # Sanity check MIME and path handling via API
    from unittest.mock import patch
    with patch.dict("os.environ", {"WOW_DATA_DIR": str(tmp_path)}):
        client = TestClient(app)
        response = client.get(
            f"/api/v1/compositions/{job['job_id']}/export?version=1"
        )
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as output:
        assert "project_manifest.json" in output.namelist()


def test_export_refuses_invalid_version(tmp_path):
    job = GenerationService(tmp_path).create(default_blueprint("demo"))
    try:
        build_project_archive(tmp_path, job["job_id"], 500)
    except ValueError as exc:
        assert "version" in str(exc)
    else:
        raise AssertionError("Unknown version unexpectedly exported")

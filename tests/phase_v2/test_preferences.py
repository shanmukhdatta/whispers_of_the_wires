"""Preference suggestions require real feedback; no default invented favorites."""
from fastapi.testclient import TestClient

from wow.api import app
from wow.contracts import default_blueprint


def test_unrated_account_has_no_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    assert not client.get("/api/v1/preferences").json()["sufficient_data"]


def test_feedback_leads_to_qualified_mood_suggestion(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    job = client.post("/api/v1/jobs", json=default_blueprint("story").model_dump()).json()
    for match in [4, 5, 4]:
        result = client.post("/api/v1/feedback", json={
            "composition_id": job["job_id"], "version": 1, "section_id": "A",
            "mood_match": match, "musical_coherence": 4,
        })
        assert result.status_code == 201, result.text
    recommendation = client.get("/api/v1/preferences").json()
    assert recommendation["recommendations"][0]["mood"] == "nervous"
    assert recommendation["recommendations"][0]["count"] == 3


def test_reject_nonexistent_section_and_cancel_cloud_job(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    bp = default_blueprint("story")
    job = client.post("/api/v1/jobs", json=bp.model_dump()).json()
    rating = client.post("/api/v1/feedback", json={
        "composition_id": job["job_id"], "version": 1, "section_id": "Z",
        "mood_match": 5, "musical_coherence": 5,
    })
    assert rating.status_code == 422
    bp.generation.provider = "midigpt"
    bp.generation.checkpoint = "yellow_medium"
    cloud = client.post("/api/v1/jobs", json=bp.model_dump()).json()
    cancellation = client.post(f"/api/v1/jobs/{cloud['job_id']}/cancel")
    assert cancellation.status_code == 200
    assert cancellation.json()["state"] == "cancelled"
    assert client.post(f"/api/v1/jobs/{cloud['job_id']}/cancel").status_code == 409

"""Evaluation separates measured musical properties from human emotion judgements."""
from fastapi.testclient import TestClient

from wow.api import app
from wow.contracts import default_blueprint


def test_evaluation_and_subjective_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    bp = default_blueprint("calm after a stressful day")
    job = client.post("/api/v1/jobs", json=bp.model_dump()).json()["job_id"]
    report = client.post("/api/v1/evaluations", json={
        "composition_id": job, "version": 1,
    })
    assert report.status_code == 200, report.text
    result = report.json()
    assert result["objective"]["tracks"] == 4
    assert len(result["objective"]["sections"]) == 3
    assert result["subjective"]["emotion_alignment"] is None
    assert result["objective"]["wav_rms"] > 0
    rating = client.post("/api/v1/feedback", json={
        "composition_id": job, "version": 1, "section_id": "A",
        "mood_match": 3, "musical_coherence": 4,
    })
    assert rating.status_code == 201, rating.text
    summary = client.get(f"/api/v1/feedback/summary/{job}").json()
    assert summary["sections"][0]["n_ratings"] == 1
    assert summary["sections"][0]["avg_mood_match"] == 3.0


def test_feedback_score_boundaries(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    assert client.post("/api/v1/feedback", json={
        "composition_id": "x", "version": 1, "section_id": "A",
        "mood_match": 7, "musical_coherence": 3,
    }).status_code == 422

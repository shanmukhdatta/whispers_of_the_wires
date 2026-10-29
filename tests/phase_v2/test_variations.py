"""No GPU needed to create deterministic alternatives and extensions."""
from fastapi.testclient import TestClient

from wow.api import app
from wow.contracts import default_blueprint
from wow.variations import VariationRequest, vary


def test_varied_blueprint_extends_last_section():
    base = default_blueprint("anxious then confident")
    generated = vary(base, VariationRequest(seed=199, extend_bars=4))
    assert generated.total_bars == 16
    assert generated.sections[-1].bar_count == 8
    assert base.total_bars == 12
    assert base.generation.seed != generated.generation.seed


def test_batch_and_variation_api(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    input_blueprint = default_blueprint("a story").model_dump()
    batch = client.post("/api/v1/jobs/batch", json={
        "blueprints": [input_blueprint, input_blueprint]
    })
    assert batch.status_code == 202, batch.text
    assert batch.json()["count"] == 2
    first = batch.json()["jobs"][0]
    assert first["state"] == "completed"
    assert first["data"]["elapsed_seconds"] >= 0
    variation = client.post(
        f"/api/v1/compositions/{first['job_id']}/variations",
        json={"seed": 200, "extend_bars": 4},
    )
    assert variation.status_code == 202, variation.text
    assert variation.json()["source_composition_id"] == first["job_id"]
    assert variation.json()["state"] == "completed"
    evaluation = client.post("/api/v1/evaluations", json={
        "composition_id": first["job_id"], "version": 1
    })
    assert evaluation.status_code == 200
    measured = evaluation.json()["objective"]
    assert 0 <= measured["constraint_score_0_to_100"] <= 100
    assert "NOT a mood" in measured["constraint_score_definition"]

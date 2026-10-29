"""The PDF's contextual environment/activity and VAD mood-dimension contracts."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from wow.api import app
from wow.composer import compose_rule_based
from wow.context import extract_context
from wow.contracts import MusicBlueprint, default_blueprint
from wow.planning import PlanningRequest, build_blueprint


def test_extract_explicit_context():
    ctx = extract_context("Morning studying in the rain")
    assert ctx.activity == "study"
    assert ctx.weather == "rainy"
    assert ctx.time_of_day == "morning"
    assert ctx.source == "prompt"
    override = extract_context("rainy afternoon", weather="sunny")
    assert override.weather == "sunny"
    assert override.source == "explicit"


def test_context_in_blueprint_and_api():
    client = TestClient(app)
    bp = client.post("/api/v1/blueprints", json={
        "prompt": "night journey after rain", "context_activity": "relax",
    })
    assert bp.status_code == 200, bp.text
    assert bp.json()["context"]["activity"] == "relax"
    assert bp.json()["context"]["time_of_day"] == "night"
    context = client.post("/api/v1/context", json={
        "prompt": "morning studying in rain",
    })
    assert context.status_code == 200
    assert context.json()["context"]["weather"] == "rainy"


def test_dominance_bounds_and_reviewable_dimension():
    blueprint = default_blueprint("calm music")
    data = blueprint.model_dump()
    data["sections"][0]["dominance"] = 0.5
    assert MusicBlueprint.model_validate(data).sections[0].dominance == 0.5
    data["sections"][0]["dominance"] = 1.5
    with pytest.raises(ValidationError):
        MusicBlueprint.model_validate(data)


def test_contextual_controls_have_real_cpu_effect():
    base = build_blueprint(PlanningRequest(
        prompt="peaceful evening", moods=["peaceful"],
    ))
    relax = build_blueprint(PlanningRequest(
        prompt="peaceful evening", moods=["peaceful"], context_activity="relax",
    ))
    assert base.context.activity is None
    assert relax.context.activity == "relax"
    first = compose_rule_based(base).instruments[0].notes
    second = compose_rule_based(relax).instruments[0].notes
    assert sum(n.velocity for n in second) < sum(n.velocity for n in first)

"""Deterministic planning tests: user correction and no unverifiable mood certainty."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from wow.api import app
from wow.emotion import analyze_prompt, normalize_mood
from wow.planning import PlanningRequest, build_blueprint


def test_prompt_mood_progression():
    feelings = analyze_prompt("I feel anxious, then confident, finally relieved")
    assert [x.mood for x in feelings] == ["nervous", "confident", "relieved"]


def test_ambiguous_mood_requests_review():
    result = normalize_mood("under the stars with glowing wires")
    assert result.needs_review
    assert not result.evidence


def test_manual_override_and_contiguous_sections():
    request = PlanningRequest(prompt="A story", moods=["sad", "joyful", "peaceful"],
                              total_bars=14)
    blueprint = build_blueprint(request)
    assert [(s.start_bar, s.bar_count) for s in blueprint.sections] == [
        (0, 5), (5, 5), (10, 4)
    ]


def test_blueprint_invalid_meter_or_bars():
    with pytest.raises(ValidationError):
        PlanningRequest(prompt="Example", total_bars=2)
    with pytest.raises(ValidationError):
        PlanningRequest(prompt="Example", moods=["sad"] * 5)


def test_phase2_endpoints():
    client = TestClient(app)
    result = client.post("/api/v1/analyze", json={"prompt": "anxious then relieved"})
    assert result.status_code == 200
    assert len(result.json()["segments"]) == 2
    bp = client.post("/api/v1/blueprints",
                     json={"prompt": "Example", "moods": ["joyful", "peaceful"]})
    assert bp.status_code == 200
    assert [s["mood"] for s in bp.json()["sections"]] == ["joyful", "peaceful"]

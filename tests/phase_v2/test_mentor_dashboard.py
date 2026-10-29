"""Mentor demo acceptance: controllable styles, durable library and UI boot."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from wow.composer import compose_rule_based
from wow.contracts import MusicBlueprint, default_blueprint
from wow.generation import GenerationService
from wow.planning import PlanningRequest, build_blueprint
from wow.project_archive import build_project_archive


@pytest.mark.parametrize("style", ["cinematic", "ambient", "lofi", "upbeat", "classical"])
def test_each_style_generates_valid_four_track_composition(tmp_path, style):
    plan = build_blueprint(PlanningRequest(
        prompt="nervous then confident then relieved",
        style=style, key="G_major", seed=101,
    ))
    assert plan.style == style
    job = GenerationService(tmp_path / style).create(plan)
    assert job["state"] == "completed", job
    directory = tmp_path / style / "artifacts" / job["job_id"]
    assert (directory / "composition.mid").stat().st_size > 0
    assert (directory / "composition.wav").stat().st_size > 0
    assert len(compose_rule_based(plan).instruments) == 4


def test_style_differences_and_seed_reproducibility():
    plan = default_blueprint("mood journey")
    plan.style = "ambient"
    ambient = compose_rule_based(plan)
    before = [(n.pitch, n.start, n.end, n.velocity)
              for n in compose_rule_based(plan).instruments[0].notes]
    after = [(n.pitch, n.start, n.end, n.velocity)
             for n in ambient.instruments[0].notes]
    assert before == after
    plan.style = "upbeat"
    upbeat = compose_rule_based(plan)
    assert len(upbeat.instruments[0].notes) > len(ambient.instruments[0].notes)


def test_invalid_styles_and_keys_rejected():
    with pytest.raises(ValidationError):
        build_blueprint(PlanningRequest(prompt="calm", style="unknown"))
    with pytest.raises(ValidationError):
        MusicBlueprint.model_validate({
            **default_blueprint("calm").model_dump(), "key": "H_major"
        })


def test_library_favorites_survive_restart_and_export(tmp_path):
    first = GenerationService(tmp_path)
    a = first.create(default_blueprint("nervous then relieved"))
    b = first.create(default_blueprint("joyful then calm"))
    assert a["state"] == b["state"] == "completed"
    first.jobs.set_favorite(a["job_id"], True)
    another_instance = GenerationService(tmp_path)
    assert [j["job_id"] for j in another_instance.jobs.list_recent()][:2] == [
        b["job_id"], a["job_id"]
    ]
    assert another_instance.jobs.favorites() == {a["job_id"]}
    archive = build_project_archive(tmp_path, a["job_id"])
    assert archive.is_file()
    another_instance.jobs.set_favorite(a["job_id"], False)
    assert not GenerationService(tmp_path).jobs.favorites()


def test_dashboard_can_boot_in_streamlit_testing(tmp_path, monkeypatch):
    monkeypatch.setenv("WOW_DATA_DIR", str(tmp_path))
    from streamlit.testing.v1 import AppTest

    dashboard = Path(__file__).resolve().parents[2] / "mentor_dashboard.py"
    at = AppTest.from_file(str(dashboard), default_timeout=30).run()
    assert not at.exception, [str(exc.message) for exc in at.exception]
    assert "Compose" in [str(item.value) for item in at.radio]

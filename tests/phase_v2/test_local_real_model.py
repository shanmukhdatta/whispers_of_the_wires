"""Direct model execution never silently replaces a missing checkpoint with rules."""
import pytest

from wow.contracts import GenerationSpec, default_blueprint
from wow.generation import GenerationService


def test_runner_rejects_rule_based_job(tmp_path):
    from scripts.run_local_model_job import run_local_model_job

    cpu = GenerationService(tmp_path).create(default_blueprint("happy"))
    with pytest.raises(ValueError, match="pending"):
        run_local_model_job(tmp_path, cpu["job_id"])


def test_runner_preserves_pending_job_when_model_fails(tmp_path, monkeypatch):
    from scripts.run_local_model_job import run_local_model_job

    blueprint = default_blueprint("relaxed rain")
    blueprint.generation = GenerationSpec(provider="midigpt", checkpoint="yellow_medium")
    job = GenerationService(tmp_path).create(blueprint)
    def interrupted(*args, **kwargs):
        raise RuntimeError("No license-approved checkpoint available")
    monkeypatch.setattr("scripts.run_local_model_job.subprocess.run", interrupted)
    with pytest.raises(RuntimeError, match="No license"):
        run_local_model_job(tmp_path, job["job_id"])
    assert GenerationService(tmp_path).jobs.get(job["job_id"])["state"] == "awaiting_cloud"

"""Cloud integration contract tests require no actual Kaggle connection."""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from wow.cloud_jobs import collect, prepare, push, status
from wow.contracts import GenerationSpec, default_blueprint
from wow.generation import GenerationService


def pending_job(tmp_path: Path) -> str:
    bp = default_blueprint("Nervous then joyful then peaceful")
    bp.generation = GenerationSpec(provider="midigpt", checkpoint="yellow_medium")
    return GenerationService(tmp_path).create(bp)["job_id"]


def test_prepare_private_kernel(tmp_path, monkeypatch):
    job_id = pending_job(tmp_path)
    # The adapter locates sources relative to its installed location, not cwd.
    bundle = prepare(tmp_path, job_id, "student_dev")
    metadata = json.loads((bundle / "kernel-metadata.json").read_text())
    assert metadata["is_private"] and metadata["enable_gpu"]
    assert metadata["id"].startswith("student_dev/")
    assert (bundle / "blueprint.json").exists()
    assert (bundle / "run.py").exists()
    assert (bundle / "src/wow/contracts.py").exists()


def test_reject_invalid_username_and_non_pending_job(tmp_path):
    job = pending_job(tmp_path)
    with pytest.raises(ValueError):
        prepare(tmp_path, job, "username/other")
    with pytest.raises(ValueError):
        prepare(tmp_path, "not-a-uuid", "user")


def test_kaggle_commands_are_explicit(tmp_path, monkeypatch):
    job = pending_job(tmp_path)
    bundle = prepare(tmp_path, job, "student_dev")
    runner = Mock(return_value=Mock(stdout="queued\n"))
    monkeypatch.setattr("wow.cloud_jobs.subprocess.run", runner)
    assert push(bundle).startswith("student_dev/")
    assert status("student_dev/wow-music") == "queued"
    assert runner.call_count == 2
    kwargs = runner.call_args.kwargs
    assert kwargs["check"] and kwargs["timeout"] == 180
    with pytest.raises(ValueError):
        status("bad;rm/other")


def test_collect_requires_real_manifest(tmp_path, monkeypatch):
    job = pending_job(tmp_path)
    monkeypatch.setattr("wow.cloud_jobs._run_cli", Mock(return_value=""))
    with pytest.raises(ValueError, match="manifest"):
        collect(tmp_path, job, "student_dev/wow-music")

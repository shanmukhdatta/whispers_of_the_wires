"""Cloud integration contract tests require no actual Kaggle connection."""
import json
import os
import subprocess
import sys
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


def test_single_file_kernel_extracts_every_resource(tmp_path):
    """Proves Kaggle's uploaded code_file alone carries blueprint + Python package."""
    job = pending_job(tmp_path)
    bundle = prepare(tmp_path, job, "student_dev")
    remote = tmp_path / "simulated_kaggle_working"
    env = dict(os.environ)
    env["WOW_KAGGLE_WORKING"] = str(remote)
    subprocess.run(
        [sys.executable, str(bundle / "run.py"), "--extract-only"],
        env=env, check=True, timeout=20, capture_output=True,
    )
    original = (bundle / "blueprint.json").read_bytes()
    assert (remote / "blueprint.json").read_bytes() == original
    assert (remote / "batch_generate.py").read_bytes() == (
        bundle / "batch_generate.py"
    ).read_bytes()
    assert (remote / "src/wow/contracts.py").is_file()
    assert (remote / "src/wow/cloud_jobs.py").is_file()
    bp = json.loads((remote / "blueprint.json").read_text())
    assert bp["generation"]["provider"] == "midigpt"


def test_kaggle_cli_requests_a_gpu_explicitly(tmp_path, monkeypatch):
    job = pending_job(tmp_path)
    bundle = prepare(tmp_path, job, "student_dev")
    runner = Mock(return_value=Mock(stdout="kernel pushed"))
    monkeypatch.setattr("wow.cloud_jobs.subprocess.run", runner)
    push(bundle)
    called = runner.call_args.args[0]
    assert called[-2:] == ["--accelerator", "NvidiaTeslaT4"]

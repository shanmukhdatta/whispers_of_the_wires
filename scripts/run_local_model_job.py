"""Execute actual published MIDI-GPT inference in a local Python environment.

No rule-based fallback; missing pretrained model access or engine errors fail.
Only a checksum-validated model output is imported as a completed job.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from wow.generation import GenerationService


def run_local_model_job(root: Path, job_id: str, *, timeout: int = 3600) -> dict:
    """Run a pending model job in a separate Python process."""
    if not 60 <= timeout <= 7200:
        raise ValueError("Timeout must be between one minute and two hours")
    service = GenerationService(root)
    job = service.jobs.get(job_id)
    if not job or job["provider"] != "midigpt" or job["state"] != "awaiting_cloud":
        raise ValueError("Only pending MIDI-GPT jobs can be executed")
    blueprint = service.root / "artifacts" / job_id / "blueprint.json"
    if not blueprint.is_file():
        raise FileNotFoundError("Pending job blueprint missing")
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "notebooks" / "kaggle" / "batch_generate.py"
    if not script.is_file():
        raise FileNotFoundError("Model runner missing from checkout")
    with tempfile.TemporaryDirectory(prefix="wow_real_model_") as directory:
        working = Path(directory)
        shutil.copyfile(blueprint, working / "blueprint.json")
        env = dict(os.environ)
        env["WOW_KAGGLE_WORKING"] = str(working)
        subprocess.run(
            [sys.executable, str(script)],
            cwd=repo_root, env=env, check=True, timeout=timeout,
        )
        generated = working / "job-output"
        if not (generated / "manifest.json").is_file():
            raise RuntimeError("Model did not create an output manifest")
        target = service.root / "incoming" / f"local_{job_id[:8]}"
        if target.exists():
            raise FileExistsError("An import with this job ID is already staged")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(generated, target)
    return service.import_kaggle(job_id, target.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id")
    parser.add_argument("--root", type=Path, default=Path(".wow_workspace"))
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    print(run_local_model_job(args.root, args.job_id, timeout=args.timeout))


if __name__ == "__main__":
    main()

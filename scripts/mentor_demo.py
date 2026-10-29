"""Generate factual CPU demo evidence, never fabricated model or listener outcomes."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from wow.composer import validate_midi
from wow.contracts import default_blueprint
from wow.evaluation import evaluate_files
from wow.generation import GenerationService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(".wow_workspace/mentor"))
    args = parser.parse_args()
    service = GenerationService(args.output)
    blueprint = default_blueprint(
        "Nervous before an exam, then confident, finally relieved"
    )
    start = time.perf_counter()
    job = service.create(blueprint)
    if job["state"] != "completed":
        raise RuntimeError(f"CPU demo failed: {job}")
    folder = service.root / "artifacts" / job["job_id"]
    evidence = {
        "provider": "rule_based",
        "job_id": job["job_id"],
        "elapsed_seconds": round(time.perf_counter() - start, 4),
        "midi": validate_midi(folder / "composition.mid", expected_tracks=4),
        "evaluation": evaluate_files(
            folder / "composition.mid", folder / "composition.wav", blueprint
        ),
        "kaggle_model_execution_verified": False,
        "human_listening_results_available": False,
    }
    output = service.root / "mentor_evidence.json"
    output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"CPU demo evidence written: {output}")


if __name__ == "__main__":
    main()

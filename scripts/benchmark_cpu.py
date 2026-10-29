"""Measure actual CPU backend performance; no invented GPU or accuracy figures."""
from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

from wow.contracts import MusicBlueprint
from wow.evaluation import evaluate_files
from wow.generation import GenerationService
from wow.planning import PlanningRequest, build_blueprint

PROMPTS = [
    "Nervous before an exam, then confident, finally relieved",
    "Peaceful morning while reading",
    "Joyful celebration after a hard day",
    "Mysterious night journey, then hopeful",
    "Sad rainy evening, then peaceful",
    "Excited for a new adventure, then calm",
]


def run_benchmark(output: Path) -> dict:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory() as tmp:
        service = GenerationService(Path(tmp))
        for seed, prompt in enumerate(PROMPTS):
            plan = build_blueprint(PlanningRequest(prompt=prompt, seed=100 + seed))
            blueprint = MusicBlueprint.model_validate(plan.model_dump())
            start = time.perf_counter()
            result = service.create(blueprint)
            elapsed = time.perf_counter() - start
            if result["state"] != "completed":
                raise RuntimeError(f"Benchmark composition failed: {result}")
            folder = service.root / "artifacts" / result["job_id"]
            quality = evaluate_files(
                folder / "composition.mid", folder / "composition.wav", blueprint
            )
            records.append({
                "prompt": prompt, "seed": blueprint.generation.seed,
                "actual_seconds": round(elapsed, 4),
                "notes_by_track": quality["objective"]["notes_by_track"],
                "constraint_score": quality["objective"]["constraint_score_0_to_100"],
                "provider": "rule_based",
            })
    timings = sorted(x["actual_seconds"] for x in records)
    report = {
        "provider": "rule_based", "n": len(records),
        "mean_seconds": round(statistics.mean(timings), 4),
        "median_seconds": round(statistics.median(timings), 4),
        "max_seconds": round(max(timings), 4),
        "runs": records,
        "limitations": (
            "CPU local workflow only. No claim about Kaggle neural latency, "
            "user satisfaction or music emotion alignment."
        ),
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path(".wow_workspace/cpu_benchmark.json")
    )
    args = parser.parse_args()
    result = run_benchmark(args.output)
    print(f"Measured {result['n']} CPU compositions; results at {args.output}")


if __name__ == "__main__":
    main()

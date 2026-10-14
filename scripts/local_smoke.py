"""Local release smoke-test: no pretrained checkpoint or cloud access needed."""
from __future__ import annotations

import tempfile
from pathlib import Path

from wow.contracts import default_blueprint
from wow.editing import EditRequest, create_edit_version
from wow.evaluation import evaluate_files
from wow.generation import GenerationService


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = GenerationService(root)
        bp = default_blueprint("Nervous, then confident, finally relieved")
        original = store.create(bp)
        assert original["state"] == "completed", original
        job = original["job_id"]
        update = create_edit_version(
            root, job, EditRequest(
                base_version=1, track_ids=["harmony"],
                start_bar=4, end_bar_exclusive=8, operation="more_energy",
            ),
        )
        assert update["version"] == 2
        folder = root / "artifacts" / job / "versions" / "v2"
        report = evaluate_files(
            folder / "composition.mid", folder / "composition.wav", bp
        )
        assert report["objective"]["tracks"] == 4
        print("CPU pipeline smoke test passed. Cloud path NOT tested.")


if __name__ == "__main__":
    main()

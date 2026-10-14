"""Generation routing: explicit CPU baseline or staged Kaggle export; no silent fallback."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from wow.artifacts import verify_manifest, write_manifest
from wow.composer import compose_rule_based, save_midi, validate_midi
from wow.contracts import MusicBlueprint
from wow.persistence import JobStore
from wow.rendering import render_wav


class GenerationService:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.jobs = JobStore(self.root)

    def create(self, blueprint: MusicBlueprint) -> dict:
        job_id = str(uuid.uuid4())
        provider = blueprint.generation.provider
        directory = self.root / "artifacts" / job_id
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "blueprint.json").write_text(
            blueprint.model_dump_json(indent=2), encoding="utf-8"
        )
        if provider == "midigpt":
            # Dispatch is user-initiated via Kaggle CLI/UI; no persistent server is claimed.
            info = {"message": "Submit blueprint.json with Kaggle notebook; import outputs later",
                    "job_id": job_id}
            self.jobs.save(job_id, state="awaiting_cloud", provider=provider,
                           request_id=blueprint.request_id, data=info)
            return self.jobs.get(job_id)
        self.jobs.save(job_id, state="running", provider=provider,
                       request_id=blueprint.request_id, data={})
        try:
            midi = save_midi(compose_rule_based(blueprint), directory / "composition.mid")
            metrics = validate_midi(midi, expected_tracks=len(blueprint.tracks))
            wav = render_wav(midi, directory / "composition.wav")
            write_manifest(
                directory, request_id=blueprint.request_id, provider="rule_based",
                checkpoint="rule_based_v1", seed=blueprint.generation.seed,
                filenames=[midi.name, wav.name],
            )
            state = "completed"
            data = {"metrics": metrics, "assets": ["composition.mid", "composition.wav"]}
        except (OSError, ValueError, RuntimeError) as exc:
            state = "failed"
            data = {"error_code": "GENERATION_FAILED", "message": str(exc)}
        self.jobs.save(job_id, state=state, provider=provider,
                       request_id=blueprint.request_id, data=data)
        return self.jobs.get(job_id)

    def import_kaggle(self, job_id: str, folder_name: str) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError("Job not found")
        if job["provider"] != "midigpt" or job["state"] != "awaiting_cloud":
            raise ValueError("Job is not awaiting a MIDI-GPT import")
        if not folder_name or not folder_name.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Unsafe import folder name")
        source = (self.root / "incoming" / folder_name).resolve()
        expected_root = (self.root / "incoming").resolve()
        if source.parent != expected_root or not source.is_dir():
            raise ValueError("Import folder must be under incoming")
        manifest = verify_manifest(source)
        if manifest["request_id"] != job["request_id"]:
            raise ValueError("Manifest request ID mismatch")
        if manifest["provider"] != "midigpt" or manifest["checkpoint"] != "yellow_medium":
            raise ValueError("Incorrect model provenance")
        if "composition.mid" not in manifest["outputs"]:
            raise ValueError("Missing MIDI artifact")
        validate_midi(source / "composition.mid")
        target = self.root / "artifacts" / job_id
        shutil.copyfile(source / "composition.mid", target / "composition.mid")
        render_wav(target / "composition.mid", target / "composition.wav")
        self.jobs.save(
            job_id, state="completed", provider="midigpt",
            request_id=job["request_id"],
            data={"assets": ["composition.mid", "composition.wav"],
                  "checkpoint": "yellow_medium", "imported_from": folder_name},
        )
        return self.jobs.get(job_id)

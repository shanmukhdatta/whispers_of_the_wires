"""Blind, anonymous listening-study package and descriptive evaluation.

A study packet never includes the provider/seed key; only the organizer keeps
the mapping. Source audio remains unchanged. No ratings are invented here.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

from wow.generation import GenerationService

RATING_HEADER = ["stimulus_id", "participant_code", "mood_match", "musical_coherence"]


def build_study(root: Path, output: Path, *, seed: int = 1729, limit: int = 20) -> dict:
    if not 2 <= limit <= 20:
        raise ValueError("Study size must be between 2 and 20")
    manager = GenerationService(root)
    jobs = [x for x in manager.jobs.list_jobs(limit=250) if x["state"] == "completed"]
    songs = []
    for job in jobs:
        wav = manager.root / "artifacts" / job["job_id"] / "composition.wav"
        blueprint = manager.root / "artifacts" / job["job_id"] / "blueprint.json"
        if wav.is_file() and blueprint.is_file():
            parsed = json.loads(blueprint.read_text(encoding="utf-8"))
            songs.append((job, wav, parsed))
    if len(songs) < 2:
        raise ValueError("At least two completed local compositions are needed")
    rng = random.Random(seed)
    rng.shuffle(songs)
    songs = songs[:limit]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    packet = output / "blind_listening_pack.zip"
    key = []
    with zipfile.ZipFile(packet, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for position, (job, wav, bp) in enumerate(songs, start=1):
            stimulus_id = "S" + hashlib.sha256(
                f"{seed}:{job['job_id']}:{position}".encode()
            ).hexdigest()[:10].upper()
            output_name = f"audio/{stimulus_id}.wav"
            bundle.write(wav, arcname=output_name)
            key.append({
                "stimulus_id": stimulus_id, "composition_id": job["job_id"],
                "provider": job["provider"], "prompt": bp["prompt"],
                "sections": [s["mood"] for s in bp["sections"]],
                "source_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
            })
        template = io.StringIO()
        writer = csv.DictWriter(template, fieldnames=RATING_HEADER)
        writer.writeheader()
        bundle.writestr("ratings_template.csv", template.getvalue())
        bundle.writestr(
            "READ_ME_FIRST.txt",
            "Optional anonymous music listening study.\n"
            "Listen to each WAV without knowing which algorithm made it.\n"
            "Enter stimulus_id, a random non-identifying participant_code,\n"
            "mood_match (1-5), musical_coherence (1-5).\n"
            "Use no names, emails, phone numbers or addresses.\n"
            "Participants may opt out or skip a clip.\n"
            "Scores are subjective ratings, not validated model accuracy.\n",
        )
    key_file = output / "PRIVATE_stimulus_key.json"
    key_file.write_text(json.dumps(key, indent=2), encoding="utf-8")
    return {
        "zip": str(packet), "private_key": str(key_file),
        "stimuli": len(key), "providers": sorted({k["provider"] for k in key}),
    }


def analyze_study(key_file: Path, ratings_file: Path) -> dict:
    key = json.loads(Path(key_file).read_text(encoding="utf-8"))
    lookup = {x["stimulus_id"]: x for x in key}
    if not lookup or len(lookup) != len(key):
        raise ValueError("Invalid private stimulus mapping")
    observations: dict[str, list[dict[str, int]]] = {}
    seen = set()
    participants = set()
    with Path(ratings_file).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(RATING_HEADER).issubset(reader.fieldnames):
            raise ValueError("Ratings file requires all template columns")
        for row in reader:
            stimulus_id = (row.get("stimulus_id") or "").strip()
            participant_code = (row.get("participant_code") or "").strip()
            if stimulus_id not in lookup or not 3 <= len(participant_code) <= 30:
                raise ValueError("Unknown stimulus or invalid anonymous participant code")
            key_tuple = (stimulus_id, participant_code)
            if key_tuple in seen:
                raise ValueError("Duplicate rating by one participant for a stimulus")
            seen.add(key_tuple)
            participants.add(participant_code)
            mood = int(row["mood_match"])
            coherence = int(row["musical_coherence"])
            if not 1 <= mood <= 5 or not 1 <= coherence <= 5:
                raise ValueError("Ratings must be between 1 and 5")
            provider = lookup[stimulus_id]["provider"]
            observations.setdefault(provider, []).append({
                "mood": mood, "coherence": coherence,
            })
    if not seen:
        raise ValueError("No actual listener ratings provided")
    summaries = []
    for provider, ratings in sorted(observations.items()):
        n = len(ratings)
        summaries.append({
            "provider": provider,
            "n_ratings": n,
            "mean_mood_rating_1_to_5": round(
                sum(x["mood"] for x in ratings) / n, 3
            ),
            "mean_coherence_rating_1_to_5": round(
                sum(x["coherence"] for x in ratings) / n, 3
            ),
            "insufficient_pilot_data": n < 10,
        })
    return {
        "rating_records": len(seen),
        "distinct_anonymous_participant_codes": len(participants),
        "by_provider": summaries,
        "limitations": (
            "Descriptive survey, not proof of emotion-recognition accuracy; "
            "compare only under a prespecified balanced study protocol."
        ),
    }

"""Single-user, evidence-limited mood preferences from explicit listener feedback."""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def recommend_moods(root: Path, minimum_ratings: int = 3) -> dict:
    root = Path(root)
    db_path = root / "feedback.sqlite3"
    if not db_path.is_file():
        return {"based_on_ratings": 0, "recommendations": [], "sufficient_data": False}
    with sqlite3.connect(db_path) as database:
        rows = database.execute(
            "SELECT composition_id, section_id, mood_match, musical_coherence "
            "FROM ratings"
        ).fetchall()
    moods: dict[str, list[float]] = defaultdict(list)
    for composition_id, section_id, alignment, musicality in rows:
        path = root / "artifacts" / composition_id / "blueprint.json"
        if not path.is_file():
            continue
        try:
            sections = json.loads(path.read_text(encoding="utf-8")).get("sections", [])
            section = next(s for s in sections if s.get("id") == section_id)
            mood = section["mood"]
        except (OSError, ValueError, KeyError, StopIteration, TypeError):
            continue
        moods[mood].append((float(alignment) + float(musicality)) / 2)
    ranked = sorted(
        [
            {"mood": mood, "count": len(scores), "average_rating": round(
                sum(scores) / len(scores), 3
            )}
            for mood, scores in moods.items() if len(scores) >= minimum_ratings
        ],
        key=lambda record: (-record["average_rating"], -record["count"], record["mood"]),
    )
    return {
        "based_on_ratings": sum(len(scores) for scores in moods.values()),
        "minimum_ratings_per_mood": minimum_ratings,
        "recommendations": ranked[:5],
        "sufficient_data": bool(ranked),
        "method": "descriptive past ratings, not a trained music preference model",
    }

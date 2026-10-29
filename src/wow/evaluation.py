"""Separate objective MIDI/audio diagnostics from voluntary subjective listener ratings."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pretty_midi
import soundfile as sf
from pydantic import BaseModel, Field

from wow.contracts import MusicBlueprint


def evaluate_files(midi_path: Path, wav_path: Path, blueprint: MusicBlueprint) -> dict:
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    audio, sample_rate = sf.read(str(wav_path), always_2d=True)
    if len(audio) == 0:
        raise ValueError("Empty audio")
    counts: dict[str, int] = {track.id: 0 for track in blueprint.tracks}
    pitch_classes = [0] * 12
    per_section = []
    for section in blueprint.sections:
        start = section.start_bar * 4 * 60 / blueprint.tempo_bpm
        end = (section.start_bar + section.bar_count) * 4 * 60 / blueprint.tempo_bpm
        selected = [
            note for ins in midi.instruments for note in ins.notes
            if start <= note.start < end
        ]
        per_section.append({
            "id": section.id, "requested_mood": section.mood,
            "notes": len(selected),
            "onsets_per_bar": round(len(selected) / section.bar_count, 4),
            "mean_velocity": (
                round(sum(n.velocity for n in selected) / len(selected), 4)
                if selected else None
            ),
            "perceived_emotion": None,
        })
    for inst in midi.instruments:
        counts[inst.name] = counts.get(inst.name, 0) + len(inst.notes)
        if not inst.is_drum:
            for note in inst.notes:
                pitch_classes[note.pitch % 12] += 1
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))
    actual_duration = len(audio) / sample_rate
    track_count = len(midi.instruments)
    expected_tracks = len(blueprint.tracks)
    tracks_present = sum(bool(x.notes) for x in midi.instruments)
    target_duration = blueprint.duration_seconds
    # This is constraint compliance, NOT a score of perceived emotion or artistry.
    duration_fraction = max(0.0, 1.0 - abs(actual_duration - target_duration)
                            / max(target_duration, 1))
    structural_fraction = min(1.0, tracks_present / max(expected_tracks, 1))
    audio_fraction = 1.0 if rms > 1e-5 and peak < 0.999 else 0.0
    constraint_score = round(
        100 * (0.5 * structural_fraction + 0.3 * duration_fraction
               + 0.2 * audio_fraction), 2
    )
    return {
        "schema_version": "1.0",
        "objective": {
            "constraint_score_0_to_100": constraint_score,
            "constraint_score_definition": (
                "50% tracks with notes, 30% duration agreement, "
                "20% non-silent unclipped audio; NOT a mood or creativity score"
            ),
            "tracks": track_count,
            "notes_by_track": counts,
            "pitch_class_counts": pitch_classes,
            "midi_duration_seconds": round(midi.get_end_time(), 4),
            "wav_duration_seconds": round(actual_duration, 4),
            "nominal_duration_seconds": blueprint.duration_seconds,
            "wav_peak": round(peak, 5),
            "wav_rms": round(rms, 5),
            "clipping_detected": bool(np.any(np.abs(audio) >= 0.999)),
            "sections": per_section,
        },
        "subjective": {
            "emotion_alignment": None,
            "human_ratings_required": True,
        },
        "caveat": "Velocity and onset density are proxies, not emotion accuracy.",
    }


class ListenerRating(BaseModel):
    composition_id: str = Field(min_length=1, max_length=64)
    version: int = Field(ge=1)
    section_id: str = Field(min_length=1, max_length=20)
    mood_match: int = Field(ge=1, le=5)
    musical_coherence: int = Field(ge=1, le=5)
    comments: str = Field(default="", max_length=500)


class FeedbackStore:
    def __init__(self, root: Path):
        self.file = Path(root) / "feedback.sqlite3"
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.file) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS ratings("
                "composition_id TEXT NOT NULL, version INTEGER NOT NULL, "
                "section_id TEXT NOT NULL, mood_match INTEGER NOT NULL, "
                "musical_coherence INTEGER NOT NULL, comments TEXT NOT NULL)"
            )

    def add(self, rating: ListenerRating) -> dict:
        with sqlite3.connect(self.file) as db:
            db.execute(
                "INSERT INTO ratings VALUES(?,?,?,?,?,?)",
                (rating.composition_id, rating.version, rating.section_id,
                 rating.mood_match, rating.musical_coherence, rating.comments),
            )
        return {"stored": True, "composition_id": rating.composition_id,
                "version": rating.version}

    def summarize(self, composition_id: str) -> dict:
        with sqlite3.connect(self.file) as db:
            rows = db.execute(
                "SELECT section_id, COUNT(*), AVG(mood_match), "
                "AVG(musical_coherence) FROM ratings WHERE composition_id=? "
                "GROUP BY section_id ORDER BY section_id",
                (composition_id,),
            ).fetchall()
        return {"composition_id": composition_id, "sections": [
            {"id": row[0], "n_ratings": row[1],
             "avg_mood_match": round(row[2], 3),
             "avg_coherence": round(row[3], 3)}
            for row in rows
        ]}

"""Versioned music composition contracts; bars use zero-based half-open intervals."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Meter(StrictModel):
    numerator: Literal[4] = 4
    denominator: Literal[4] = 4


class Section(StrictModel):
    id: str = Field(min_length=1, max_length=20)
    start_bar: int = Field(ge=0)
    bar_count: int = Field(ge=1, le=64)
    mood: str = Field(min_length=1, max_length=80)
    valence: float = Field(ge=-1, le=1)
    arousal: float = Field(ge=-1, le=1)


class TrackSpec(StrictModel):
    id: str = Field(min_length=1, max_length=40)
    program: int = Field(default=0, ge=0, le=127)
    is_drum: bool = False


class GenerationSpec(StrictModel):
    provider: Literal["rule_based", "midigpt"] = "rule_based"
    checkpoint: str = "rule_based_v1"
    seed: int = Field(default=42, ge=0, le=2**32 - 1)
    max_candidates: int = Field(default=1, ge=1, le=4)


class MusicBlueprint(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    request_id: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=2000)
    language: Literal["en"] = "en"
    mode: Literal["instrumental"] = "instrumental"
    tempo_bpm: int = Field(default=96, ge=60, le=160)
    time_signature: Meter = Field(default_factory=Meter)
    key: Literal["C_major", "G_major", "F_major", "A_minor"] = "C_major"
    total_bars: int = Field(default=12, ge=1, le=64)
    sections: list[Section] = Field(min_length=1, max_length=16)
    tracks: list[TrackSpec] = Field(min_length=1, max_length=16)
    generation: GenerationSpec = Field(default_factory=GenerationSpec)

    @model_validator(mode="after")
    def validate_structure(self) -> MusicBlueprint:
        cursor = 0
        used_sections: set[str] = set()
        for section in self.sections:
            if section.id in used_sections:
                raise ValueError("Duplicate section ID")
            used_sections.add(section.id)
            if section.start_bar != cursor:
                raise ValueError("Sections must be ordered, contiguous and start at bar 0")
            cursor += section.bar_count
        if cursor != self.total_bars:
            raise ValueError("Section bar counts must sum to total_bars")
        ids = [track.id for track in self.tracks]
        if len(ids) != len(set(ids)):
            raise ValueError("Track IDs must be unique")
        return self

    @property
    def duration_seconds(self) -> float:
        return self.total_bars * self.time_signature.numerator * 60 / self.tempo_bpm


def default_blueprint(prompt: str, request_id: str = "demo-001") -> MusicBlueprint:
    """Create a deterministic demo plan; phase 2 will replace fixed mood choices."""
    return MusicBlueprint(
        request_id=request_id,
        prompt=prompt,
        sections=[
            Section(id="A", start_bar=0, bar_count=4, mood="nervous",
                    valence=-0.6, arousal=0.7),
            Section(id="B", start_bar=4, bar_count=4, mood="confident",
                    valence=0.5, arousal=0.8),
            Section(id="C", start_bar=8, bar_count=4, mood="relieved",
                    valence=0.7, arousal=0.3),
        ],
        tracks=[
            TrackSpec(id="melody", program=0),
            TrackSpec(id="harmony", program=48),
            TrackSpec(id="bass", program=32),
            TrackSpec(id="drums", is_drum=True),
        ],
    )

"""Transform reviewed moods and user constraints into deterministic musical blueprints."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator

from wow.context import extract_context
from wow.contracts import GenerationSpec, MusicBlueprint, Section, TrackSpec
from wow.emotion import EmotionSignal, analyze_prompt, normalize_mood


class PlanningRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tempo_bpm: int = Field(default=96, ge=60, le=160)
    total_bars: int = Field(default=12, ge=3, le=64)
    key: str = "C_major"
    genre: str = "cinematic"
    context_activity: str | None = Field(default=None, max_length=40)
    context_weather: str | None = Field(default=None, max_length=40)
    context_time_of_day: str | None = Field(default=None, max_length=40)
    instrument_programs: dict[str, int] = Field(default_factory=dict)
    moods: list[str] | None = Field(default=None, min_length=1, max_length=4)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)

    @model_validator(mode="after")
    def valid_moods(self) -> PlanningRequest:
        if self.moods and len(self.moods) > self.total_bars:
            raise ValueError("Cannot assign fewer than one bar to each mood")
        if set(self.instrument_programs) - {"melody", "harmony", "bass"}:
            raise ValueError("Unknown instrument role")
        if any(not 0 <= program <= 127 for program in self.instrument_programs.values()):
            raise ValueError("Instrument program must be General MIDI 0..127")
        return self


def to_sections(signals: list[EmotionSignal], total_bars: int) -> list[Section]:
    if not signals or total_bars < len(signals):
        raise ValueError("Not enough bars for emotional sections")
    each, remainder = divmod(total_bars, len(signals))
    cursor = 0
    sections = []
    for index, signal in enumerate(signals):
        count = each + (1 if index < remainder else 0)
        sections.append(Section(
            id=chr(65 + index), start_bar=cursor, bar_count=count,
            mood=signal.mood, valence=signal.valence, arousal=signal.arousal,
        ))
        cursor += count
    return sections


def build_blueprint(request: PlanningRequest) -> MusicBlueprint:
    signals = ([normalize_mood(m) for m in request.moods]
               if request.moods else analyze_prompt(request.prompt))
    if request.total_bars < len(signals):
        raise ValueError("Total bars must cover every emotional segment")
    return MusicBlueprint(
        request_id=request.request_id,
        prompt=request.prompt,
        tempo_bpm=request.tempo_bpm,
        total_bars=request.total_bars,
        key=request.key,
        genre=request.genre,
        context=extract_context(
            request.prompt,
            activity=request.context_activity,
            weather=request.context_weather,
            time_of_day=request.context_time_of_day,
        ),
        sections=to_sections(signals, request.total_bars),
        tracks=[
            TrackSpec(id="melody", program=request.instrument_programs.get("melody", 0)),
            TrackSpec(id="harmony", program=request.instrument_programs.get("harmony", 48)),
            TrackSpec(id="bass", program=request.instrument_programs.get("bass", 32)),
            TrackSpec(id="drums", is_drum=True),
        ],
        generation=GenerationSpec(seed=request.seed),
    )

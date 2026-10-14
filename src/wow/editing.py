"""Selective MIDI editing with a provable lock-region preservation invariant."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Literal

import pretty_midi
from pydantic import BaseModel, Field, model_validator

from wow.artifacts import write_manifest
from wow.composer import validate_midi
from wow.contracts import MusicBlueprint
from wow.rendering import render_wav


class EditRequest(BaseModel):
    base_version: int = Field(default=1, ge=1)
    track_ids: list[str] = Field(min_length=1)
    start_bar: int = Field(ge=0)
    end_bar_exclusive: int = Field(gt=0)
    operation: Literal["more_energy", "less_dense", "transpose_up"]

    @model_validator(mode="after")
    def validate_range(self) -> EditRequest:
        if self.end_bar_exclusive <= self.start_bar:
            raise ValueError("Edit end must be strictly after start")
        if len(self.track_ids) != len(set(self.track_ids)):
            raise ValueError("Duplicate track IDs")
        return self


def _note_tuple(note: pretty_midi.Note) -> tuple:
    return (note.pitch, round(note.start, 7), round(note.end, 7), note.velocity)


def locked_events(midi: pretty_midi.PrettyMIDI, *, tracks: set[str],
                  start: float, end: float) -> list[tuple]:
    result = []
    for instrument in midi.instruments:
        for note in instrument.notes:
            editable = (instrument.name in tracks and
                        note.start >= start - 1e-8 and note.end <= end + 1e-8)
            if not editable:
                result.append((instrument.name, instrument.program,
                               instrument.is_drum, *_note_tuple(note)))
    return sorted(result)


def selective_edit(original: pretty_midi.PrettyMIDI, blueprint: MusicBlueprint,
                   request: EditRequest) -> pretty_midi.PrettyMIDI:
    if request.end_bar_exclusive > blueprint.total_bars:
        raise ValueError("Edit bar region extends past composition")
    known = {track.id for track in blueprint.tracks}
    if not set(request.track_ids).issubset(known):
        raise ValueError("Unknown track ID")
    if (request.operation == "transpose_up"
            and any(t.is_drum for t in blueprint.tracks if t.id in request.track_ids)):
        raise ValueError("Transposition not supported for drums")
    seconds_per_bar = 4 * 60 / blueprint.tempo_bpm
    start = request.start_bar * seconds_per_bar
    end = request.end_bar_exclusive * seconds_per_bar
    before = locked_events(original, tracks=set(request.track_ids), start=start, end=end)
    changed = copy.deepcopy(original)
    modified = 0
    for instrument in changed.instruments:
        if instrument.name not in request.track_ids:
            continue
        region = [note for note in instrument.notes
                  if note.start >= start - 1e-8 and note.end <= end + 1e-8]
        if not region:
            continue
        if request.operation == "less_dense":
            # Preserve selected first and every other note; locked regions untouched.
            to_remove = {id(note) for note in region[1::2]}
            instrument.notes = [n for n in instrument.notes if id(n) not in to_remove]
            modified += len(to_remove)
        else:
            for note in region:
                if request.operation == "more_energy":
                    note.velocity = min(127, note.velocity + 18)
                else:
                    note.pitch = min(127, note.pitch + 2)
                modified += 1
    if modified == 0:
        raise ValueError("Selected region contains no editable MIDI events")
    after = locked_events(changed, tracks=set(request.track_ids), start=start, end=end)
    if before != after:
        raise ValueError("LOCKED_REGION_MODIFIED")
    return changed


def version_directory(root: Path, job_id: str, version: int) -> Path:
    if version < 1:
        raise ValueError("Invalid version")
    from uuid import UUID
    if str(UUID(job_id)) != job_id:
        raise ValueError("Invalid composition ID")
    base = Path(root).resolve() / "artifacts" / job_id
    return base if version == 1 else base / "versions" / f"v{version}"


def versions(root: Path, job_id: str) -> list[int]:
    directory = version_directory(root, job_id, 1)
    if not (directory / "composition.mid").is_file():
        return []
    result = [1]
    for file in (directory / "versions").glob("v*/composition.mid"):
        try:
            version = int(file.parent.name[1:])
        except ValueError:
            continue
        if version >= 2:
            result.append(version)
    return sorted(set(result))


def create_edit_version(root: Path, job_id: str,
                        request: EditRequest) -> dict:
    available = versions(root, job_id)
    if not available:
        raise KeyError("Composition not found")
    if request.base_version != available[-1]:
        raise ValueError("Stale base_version; edit latest version")
    directory = version_directory(root, job_id, 1)
    blueprint = MusicBlueprint.model_validate_json(
        (directory / "blueprint.json").read_text(encoding="utf-8")
    )
    source = version_directory(root, job_id, request.base_version) / "composition.mid"
    result = selective_edit(pretty_midi.PrettyMIDI(str(source)), blueprint, request)
    new_version = available[-1] + 1
    output = version_directory(root, job_id, new_version)
    output.mkdir(parents=True, exist_ok=False)
    midi_path = output / "composition.mid"
    result.write(str(midi_path))
    validate_midi(midi_path)
    render_wav(midi_path, output / "composition.wav")
    write_manifest(output, request_id=blueprint.request_id, provider="selective_edit",
                   checkpoint="edit_v1", seed=blueprint.generation.seed,
                   filenames=["composition.mid", "composition.wav"])
    return {"composition_id": job_id, "version": new_version,
            "base_version": request.base_version, "preserved_locked_events": True,
            "operation": request.operation}

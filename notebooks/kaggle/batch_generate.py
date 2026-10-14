"""Generate a complete blueprint on Kaggle using actual MIDI-GPT (no silent CPU fallback).

Run after installing this repo + midigpt[inference]; requires blueprint.json as
input at /kaggle/working/blueprint.json. Exports a checksum-validated job-output.
Use the checkpoint's 4-bar context and stitch successive 4-bar chunks.
This file is provided for a real Kaggle smoke test, NOT a verified benchmark.
"""
from __future__ import annotations

import hashlib
import json
import platform
import tempfile
from pathlib import Path
from time import perf_counter

import pretty_midi
import torch
from midigpt import Bar, Score, Track
from midigpt.inference import (
    GenerationRequest, InferenceConfig, InferenceEngine, TrackPrompt,
)
from wow.composer import validate_midi
from wow.contracts import MusicBlueprint


def main() -> None:
    started = perf_counter()
    working = Path("/kaggle/working")
    bp = MusicBlueprint.model_validate_json(
        (working / "blueprint.json").read_text(encoding="utf-8")
    )
    if bp.generation.provider != "midigpt":
        raise ValueError("Cloud generation requires provider=midigpt")
    if bp.generation.checkpoint != "yellow_medium":
        raise ValueError("Unexpected checkpoint")
    torch.manual_seed(bp.generation.seed)
    engine = InferenceEngine.from_pretrained("yellow_medium")
    output = pretty_midi.PrettyMIDI(initial_tempo=bp.tempo_bpm)
    for role in bp.tracks:
        output.instruments.append(pretty_midi.Instrument(
            program=role.program, is_drum=role.is_drum, name=role.id,
        ))
    duration_bar = 4 * 60 / bp.tempo_bpm
    for section in bp.sections:
        for offset in range(0, section.bar_count, 4):
            score = Score(tracks=[Track(bars=[Bar() for _ in range(4)])
                                  for _ in bp.tracks])
            attrs = engine._analyzer.attribute_sizes()
            size = attrs.get("note_density", 0)
            level = max(0, min(size - 1, int((section.arousal + 1) / 2 * size)))
            prompts = []
            for index in range(len(bp.tracks)):
                values = {"note_density": level} if size > 0 else {}
                prompts.append(TrackPrompt(
                    id=index, bars=[0, 1, 2, 3], attributes=values,
                ))
            result = engine.session(
                score,
                GenerationRequest(
                    tracks=prompts,
                    config=InferenceConfig(model_dim=4, mask_mode="attention"),
                ),
            ).run()
            with tempfile.TemporaryDirectory() as tmp:
                file = Path(tmp) / "chunk.mid"
                result.to_midi(str(file))
                midi = pretty_midi.PrettyMIDI(str(file))
            if len(midi.instruments) < len(bp.tracks):
                raise ValueError("Checkpoint did not generate expected track count")
            generated_bars = min(4, section.bar_count - offset)
            tempos = midi.get_tempo_changes()[1]
            if midi.get_end_time() <= 0 or len(tempos) == 0 or tempos[0] <= 0:
                raise ValueError("Invalid generated segment tempo")
            source_bar_duration = 4 * 60 / float(tempos[0])
            scale = duration_bar / source_bar_duration
            time_offset = (section.start_bar + offset) * duration_bar
            section_end = time_offset + generated_bars * duration_bar
            for index, role in enumerate(bp.tracks):
                for note in midi.instruments[index].notes:
                    start = time_offset + note.start * scale
                    end = time_offset + note.end * scale
                    if start >= section_end:
                        continue
                    output.instruments[index].notes.append(pretty_midi.Note(
                        pitch=note.pitch, velocity=note.velocity,
                        start=max(time_offset, start),
                        end=max(time_offset + 0.01, min(section_end, end)),
                    ))
    folder = working / "job-output"
    folder.mkdir(parents=True, exist_ok=True)
    midi_file = folder / "composition.mid"
    output.write(str(midi_file))
    metrics = validate_midi(midi_file, expected_tracks=len(bp.tracks))
    environment = {
        "python": platform.python_version(), "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "elapsed_seconds": perf_counter() - started,
        "model": "yellow_medium", "provider": "midigpt",
    }
    (folder / "generation_metrics.json").write_text(json.dumps(metrics, indent=2))
    (folder / "run_environment.json").write_text(json.dumps(environment, indent=2))
    (folder / "generation.log").write_text(
        "Generated with MIDI-GPT yellow_medium. No local fallback.\n"
    )
    outputs = {}
    for f in sorted(folder.iterdir()):
        if f.name == "manifest.json" or not f.is_file():
            continue
        outputs[f.name] = {
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "bytes": f.stat().st_size,
        }
    (folder / "manifest.json").write_text(json.dumps({
        "schema_version": "1.0", "request_id": bp.request_id,
        "provider": "midigpt", "checkpoint": "yellow_medium",
        "seed": bp.generation.seed, "outputs": outputs,
    }, indent=2))
    print("Generation complete", environment, metrics)


if __name__ == "__main__":
    main()

"""Run from a Kaggle cell after installing MIDI-GPT's inference dependencies.

Example setup:
    %pip install "midigpt[inference]"

This file is an experimental integration adapter; exact checkpoint API can change.
"""
from pathlib import Path
from time import perf_counter
import json
import platform

import torch
from midigpt import Score, Track, Bar
from midigpt.inference import InferenceEngine, GenerationRequest, InferenceConfig, TrackPrompt

from hashlib import sha256

folder = Path("/kaggle/working/job-output")
folder.mkdir(parents=True, exist_ok=True)
started = perf_counter()
engine = InferenceEngine.from_pretrained("yellow_medium")
score = Score(tracks=[Track(bars=[Bar() for _ in range(4)])])
request = GenerationRequest(
    tracks=[TrackPrompt(id=0, bars=[0, 1, 2, 3])],
    config=InferenceConfig(model_dim=4, mask_mode="attention"),
)
result = engine.session(score, request).run()
file = folder / "composition.mid"
result.to_midi(str(file))
if not file.exists() or file.stat().st_size == 0:
    raise RuntimeError("MIDI-GPT returned no MIDI bytes")
environment = {
    "python": platform.python_version(),
    "pytorch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "elapsed_seconds": perf_counter() - started,
}
(folder / "run_environment.json").write_text(json.dumps(environment, indent=2))
checksum = sha256(file.read_bytes()).hexdigest()
manifest = {
    "schema_version": "1.0", "request_id": "kaggle-smoke-001",
    "provider": "midigpt", "checkpoint": "yellow_medium", "seed": 42,
    "outputs": {"composition.mid": {"sha256": checksum, "bytes": file.stat().st_size}},
}
(folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("Run evidence:", environment)
print("MIDI output:", file)

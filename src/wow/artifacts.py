"""Filesystem artifacts are validated; never trust remote manifest file paths."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path, *, request_id: str, provider: str,
                   checkpoint: str, seed: int, filenames: list[str]) -> Path:
    directory = Path(directory)
    outputs = {}
    for filename in filenames:
        if Path(filename).name != filename:
            raise ValueError("Manifest artifacts must be flat filenames")
        file = directory / filename
        if not file.is_file():
            raise FileNotFoundError(file)
        outputs[filename] = {"sha256": sha256(file), "bytes": file.stat().st_size}
    manifest = {
        "schema_version": "1.0", "request_id": request_id,
        "provider": provider, "checkpoint": checkpoint, "seed": seed,
        "outputs": outputs,
    }
    target = directory / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def verify_manifest(directory: Path) -> dict[str, Any]:
    directory = Path(directory).resolve()
    data = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0" or not data.get("request_id"):
        raise ValueError("Unsupported or invalid manifest")
    files = data.get("outputs")
    if not isinstance(files, dict) or not files:
        raise ValueError("Empty manifest output list")
    for name, meta in files.items():
        if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
            raise ValueError("Unsafe artifact name")
        file = (directory / name).resolve()
        if file.parent != directory or not file.is_file():
            raise ValueError("Artifact missing or escapes output directory")
        if not isinstance(meta, dict):
            raise ValueError("Invalid artifact metadata")
        expected_hash = meta.get("sha256")
        expected_bytes = meta.get("bytes")
        if (not isinstance(expected_hash, str) or len(expected_hash) != 64
                or not isinstance(expected_bytes, int) or expected_bytes < 0):
            raise ValueError("Invalid artifact checksum metadata")
        if file.stat().st_size != expected_bytes or sha256(file) != expected_hash:
            raise ValueError("Artifact checksum mismatch")
    return data

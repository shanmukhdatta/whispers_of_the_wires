"""Export a self-contained, version-specific project bundle for offline review."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from uuid import UUID

from wow.artifacts import sha256
from wow.editing import version_directory, versions


def build_project_archive(root: Path, composition_id: str, version: int = 1) -> Path:
    if str(UUID(composition_id)) != composition_id:
        raise ValueError("Invalid composition ID")
    if version not in versions(root, composition_id):
        raise ValueError("Unknown composition version")
    base = version_directory(root, composition_id, 1)
    source = version_directory(root, composition_id, version)
    blueprint = base / "blueprint.json"
    midi = source / "composition.mid"
    wav = source / "composition.wav"
    if not all(path.is_file() for path in (blueprint, midi, wav)):
        raise ValueError("Composition files are incomplete")
    assets = {"blueprint.json": blueprint, "composition.mid": midi, "composition.wav": wav}
    for path in assets.values():
        if path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("Project artifact exceeds 100 MB export limit")
    folder = base / "exports"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"project-v{version}.zip"
    manifest = {
        "schema_version": "1.0",
        "composition_id": composition_id,
        "version": version,
        "assets": {name: {"bytes": file.stat().st_size, "sha256": sha256(file)}
                   for name, file in assets.items()},
    }
    temp = folder / f".project-v{version}.tmp"
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, file in assets.items():
                archive.write(file, arcname=name)
            archive.writestr("project_manifest.json", json.dumps(manifest, indent=2))
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return target

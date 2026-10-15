"""Final release guardrails: malformed manifest metadata is rejected gracefully."""
import json

import pytest

from wow.artifacts import verify_manifest, write_manifest


def test_invalid_manifest_metadata(tmp_path):
    (tmp_path / "composition.mid").write_bytes(b"fake")
    path = write_manifest(
        tmp_path, request_id="x", provider="midigpt",
        checkpoint="yellow_medium", seed=2, filenames=["composition.mid"],
    )
    manifest = json.loads(path.read_text())
    manifest["outputs"]["composition.mid"] = "not-a-mapping"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="metadata"):
        verify_manifest(tmp_path)


def test_file_missing_rejected(tmp_path):
    (tmp_path / "file.mid").write_bytes(b"abc")
    write_manifest(
        tmp_path, request_id="x", provider="midigpt",
        checkpoint="yellow_medium", seed=2, filenames=["file.mid"],
    )
    (tmp_path / "file.mid").unlink()
    with pytest.raises(ValueError, match="missing"):
        verify_manifest(tmp_path)

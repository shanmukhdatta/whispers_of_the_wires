"""Inspect only a locally owned or legally usable music dataset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wow.data_pipeline import inspect_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate MIDI/WAV input dataset")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("dataset_audit.json"))
    args = parser.parse_args()
    result = inspect_dataset(args.directory, max_files=args.max_files)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Inspected {result['scanned']} files, wrote {args.output}")


if __name__ == "__main__":
    main()

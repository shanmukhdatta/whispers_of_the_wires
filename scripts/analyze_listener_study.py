"""Summarize genuine blind listener ratings, with no synthetic default data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wow.listener_study import analyze_study


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("study_output/analysis.json"))
    args = parser.parse_args()
    summary = analyze_study(args.key, args.ratings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Analyzed {summary['rating_records']} genuine ratings -> {args.out}")


if __name__ == "__main__":
    main()

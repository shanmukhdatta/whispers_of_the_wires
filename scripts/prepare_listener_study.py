"""Create anonymous blinded WAV evaluation ZIP; private mapping stays local."""
from __future__ import annotations

import argparse
from pathlib import Path

from wow.listener_study import build_study


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(".wow_workspace"))
    parser.add_argument("--out", type=Path, default=Path("study_output"))
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    summary = build_study(args.root, args.out, seed=args.seed, limit=args.limit)
    print(summary)


if __name__ == "__main__":
    main()

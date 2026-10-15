"""Kaggle batch job CLI; all network-affecting commands are explicit."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from wow.cloud_jobs import collect, prepare, push, status


def main() -> None:
    parser = argparse.ArgumentParser(description="Whispers of the Wires Kaggle batch jobs")
    parser.add_argument("--root", default=os.environ.get("WOW_DATA_DIR", ".wow_workspace"))
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="Build a PRIVATE Kaggle notebook bundle")
    prep.add_argument("job_id")
    prep.add_argument("--username", required=True)
    prep.add_argument("--slug", default="wow-music")
    submission = commands.add_parser("push", help="Upload a prepared PRIVATE kernel")
    submission.add_argument("job_id")
    query = commands.add_parser("status", help="Check a running Kaggle kernel")
    query.add_argument("kernel_ref")
    download = commands.add_parser("collect", help="Download, verify and import model outputs")
    download.add_argument("job_id")
    download.add_argument("kernel_ref")
    args = parser.parse_args()
    root = Path(args.root)
    if args.command == "prepare":
        print(prepare(root, args.job_id, args.username, args.slug))
    elif args.command == "push":
        print(push(root.resolve() / "kaggle_jobs" / args.job_id))
    elif args.command == "status":
        print(status(args.kernel_ref))
    elif args.command == "collect":
        print(collect(root, args.job_id, args.kernel_ref))


if __name__ == "__main__":
    main()

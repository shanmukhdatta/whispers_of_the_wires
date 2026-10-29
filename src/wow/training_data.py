"""Validated, explicitly licensed text/mood data for optional model fine-tuning."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_labeled_csv(path: Path) -> list[dict[str, str]]:
    """Require text,label, nonempty rows, and no duplicate text in one split."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Input CSV exceeds 50 MB limit")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not {"text", "label"}.issubset(reader.fieldnames):
            raise ValueError("CSV requires 'text' and 'label' columns")
        rows: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in reader:
            text = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip().lower()
            if not 2 <= len(text) <= 2000 or not 1 <= len(label) <= 40:
                raise ValueError("Bad text/label length or missing value")
            normalized = " ".join(text.lower().split())
            if normalized in seen:
                raise ValueError("Duplicate text in the same dataset split")
            seen.add(normalized)
            rows.append({"text": text, "label": label})
    if not rows:
        raise ValueError("No labeled rows")
    return rows


def validate_labeled_splits(train_file: Path, validation_file: Path) -> dict:
    """Catch exact text overlap before fine-tuning, and record real label counts."""
    train = read_labeled_csv(train_file)
    validation = read_labeled_csv(validation_file)
    if len(train) < 8 or len(validation) < 3:
        raise ValueError("Minimum: 8 training and 3 validation samples")
    labels = sorted({row["label"] for row in train})
    if len(labels) < 2:
        raise ValueError("Training requires at least two different mood labels")
    unknown = {row["label"] for row in validation} - set(labels)
    if unknown:
        raise ValueError(f"Validation has unseen labels: {sorted(unknown)}")
    train_texts = {" ".join(row["text"].lower().split()) for row in train}
    val_texts = {" ".join(row["text"].lower().split()) for row in validation}
    if train_texts & val_texts:
        raise ValueError("Leakage: train/validation contain identical text")
    counts = {label: sum(row["label"] == label for row in train) for label in labels}
    return {
        "train": train, "validation": validation, "labels": labels,
        "train_count": len(train), "validation_count": len(validation),
        "train_label_counts": counts,
        "train_sha256": dataset_sha256(train_file),
        "validation_sha256": dataset_sha256(validation_file),
    }

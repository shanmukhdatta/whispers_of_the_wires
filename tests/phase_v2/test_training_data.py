"""No labeled corpus is bundled; validate user-provided training CSV safely."""
import csv

import pytest

from wow.training_data import validate_labeled_splits


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)


def test_labeled_dataset_contract(tmp_path):
    train = tmp_path / "train.csv"
    val = tmp_path / "val.csv"
    rows = [
        {"text": f"Calm study session {i}", "label": "calm"} for i in range(5)
    ] + [
        {"text": f"Excited celebration {i}", "label": "joy"} for i in range(5)
    ]
    _write(train, rows)
    _write(val, [
        {"text": "Resting at sunrise", "label": "calm"},
        {"text": "A wonderful surprise", "label": "joy"},
        {"text": "Studying in silence", "label": "calm"},
    ])
    result = validate_labeled_splits(train, val)
    assert result["train_count"] == 10
    assert result["validation_count"] == 3
    assert result["labels"] == ["calm", "joy"]


def test_split_leakage_rejected(tmp_path):
    train = tmp_path / "train.csv"
    val = tmp_path / "val.csv"
    _write(train, [
        {"text": f"Quiet story {i}", "label": "calm"} for i in range(5)
    ] + [
        {"text": f"Bright story {i}", "label": "joy"} for i in range(5)
    ])
    _write(val, [
        {"text": "Quiet story 1", "label": "calm"},
        {"text": "Unexpected smile", "label": "joy"},
        {"text": "A new sunrise", "label": "calm"},
    ])
    with pytest.raises(ValueError, match="Leakage"):
        validate_labeled_splits(train, val)


def test_single_label_or_missing_csv_rejected(tmp_path):
    train = tmp_path / "train.csv"
    val = tmp_path / "val.csv"
    _write(train, [
        {"text": f"Calm music {i}", "label": "calm"} for i in range(10)
    ])
    _write(val, [
        {"text": f"Calm scene {i}", "label": "calm"} for i in range(3)
    ])
    with pytest.raises(ValueError, match="two different"):
        validate_labeled_splits(train, val)
    with pytest.raises(FileNotFoundError):
        validate_labeled_splits(tmp_path / "no.csv", val)

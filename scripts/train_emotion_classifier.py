"""Optional real classifier fine-tuning, only with rights-cleared, labeled user data.

pip install -e ".[training]"
python scripts/train_emotion_classifier.py --train-csv train.csv --val-csv val.csv

This code performs actual gradient updates when executed. No synthetic metrics,
unauthorized data scraping or automatic GPU availability claims.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wow.training_data import validate_labeled_splits


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fine-tune an English text emotion classifier on labeled CSV"
    )
    parser.add_argument("--train-csv", type=Path, required=True)
    parser.add_argument("--val-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("training_output/emotion"))
    parser.add_argument(
        "--base-model", default="j-hartmann/emotion-english-distilroberta-base"
    )
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.epochs <= 20 or not 1 <= args.batch_size <= 64:
        parser.error("epochs and batch-size are outside validated ranges")
    evidence = validate_labeled_splits(args.train_csv, args.val_csv)
    try:
        import numpy as np
        import torch
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise RuntimeError('Install optional training dependencies: pip install -e ".[training]"') from exc
    labels = evidence["labels"]
    label2id = {label: index for index, label in enumerate(labels)}
    id2label = {number: label for label, number in label2id.items()}
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model, num_labels=len(labels), label2id=label2id,
        id2label=id2label, ignore_mismatched_sizes=True,
    )

    class Dataset(torch.utils.data.Dataset):
        def __init__(self, rows: list[dict[str, str]]) -> None:
            self.rows = rows

        def __len__(self) -> int:
            return len(self.rows)

        def __getitem__(self, index: int) -> dict:
            row = self.rows[index]
            features = tokenizer(
                row["text"], truncation=True, max_length=192,
            )
            features["labels"] = label2id[row["label"]]
            return features

    args.out.mkdir(parents=True, exist_ok=True)
    config = TrainingArguments(
        output_dir=str(args.out), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=2e-5, weight_decay=0.01,
        eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="accuracy",
        report_to=[], seed=42, logging_steps=10,
    )

    def metrics(output) -> dict[str, float]:
        predicted = np.argmax(output.predictions, axis=1)
        accuracy = np.mean(predicted == output.label_ids)
        return {"accuracy": float(accuracy)}

    trainer = Trainer(
        model=model,
        args=config,
        train_dataset=Dataset(evidence["train"]),
        eval_dataset=Dataset(evidence["validation"]),
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=metrics,
    )
    trainer.train()
    metrics_actual = trainer.evaluate()
    trainer.save_model(str(args.out / "final"))
    tokenizer.save_pretrained(str(args.out / "final"))
    record = {
        "base_model": args.base_model, "labels": labels,
        "train_count": evidence["train_count"],
        "validation_count": evidence["validation_count"],
        "train_sha256": evidence["train_sha256"],
        "validation_sha256": evidence["validation_sha256"],
        "train_label_counts": evidence["train_label_counts"],
        "gpu_available": torch.cuda.is_available(),
        "epochs": args.epochs, "batch_size": args.batch_size,
        "actual_validation_metrics": metrics_actual,
        "claim_scope": "Text emotion classification; NOT musical emotion accuracy",
    }
    (args.out / "training_report.json").write_text(
        json.dumps(record, indent=2, default=str), encoding="utf-8"
    )
    print(f"Trained model + real evaluation saved to {args.out}")


if __name__ == "__main__":
    main()

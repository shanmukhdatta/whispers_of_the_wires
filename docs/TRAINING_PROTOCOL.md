# Optional mood-classifier fine-tuning (original DOCX Weeks 3–4)

The original proposal explicitly asks to **train and fine-tune** the text mood
analysis model. This source file implements a real gradient-update pathway,
**not a verified completed experiment**. No labeled music emotion dataset,
validation run, checkpoint, or training scores are bundled.

## Required source data and rights
Prepare rights-cleared UTF-8 CSVs with header `text,label`:
- Train: at least 8 rows and at least 2 distinct labels.
- Validation: at least 3 rows; same label vocabulary, with no exact
  normalized text shared with training.
- Each row is a natural English situation/mood description and its human
  reviewed emotion label. Do not infer labels solely from weak keyword matches.
- Keep examples from the same story/author/context group in **only one** split.
  Exact duplicate checks alone do not catch semantic paraphrase leakage.
- If participants supply examples, obtain consent and avoid personal/sensitive
  data. Never commit private user text or unauthorized copyrighted datasets.

## Real execution

```bash
git checkout mentor-readiness-dashboard
pip install -e ".[training]"
python scripts/train_emotion_classifier.py \
  --train-csv /path/to/train.csv \
  --val-csv /path/to/val.csv \
  --out training_output/emotion \
  --epochs 2 --batch-size 8
```

Use a GPU-enabled Kaggle notebook if available; on CPU it may be slow.
The script initializes a model from the named public checkpoint and replaces
the classification head when the label count differs. It fine-tunes the
transformer on your supplied dataset, evaluates **held-out text
classification accuracy**, saves the model + tokenizer, and records
SHA-256 source hashes and factual metrics.

**Do not claim** this classifier can accurately label musical emotions:
text-emotion validation is a distinct task. Do not claim new music-generation
model weights were trained. Neural MIDI-GPT checkpoint generation and
fine-tuning are separate experiments.

## Model comparison
For a defensible experiment compare:
1. Keyword-only heuristic analyzer in `wow.emotion`.
2. Published, unmodified text-emotion classifier.
3. User-data fine-tuned classifier **only after the above training completes**.

Evaluate held-out accuracy and per-label confusion; report actual sample counts.
For music, separately compare global-mood vs segment-level blueprints using
the **same** generator, seeds and a blinded listening protocol. Unperformed
experiments are marked pending in `docs/PDF_30_DAY_COVERAGE.md`.

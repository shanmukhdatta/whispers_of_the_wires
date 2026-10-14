# Phase 2 — Emotion and Blueprint Planning

## Includes
- Transparent English keyword/mood signals with evidence and needs_review flags.
- Optional (never auto-downloaded) DistilRoBERTa classifier; output scores do **not** equal musical mood accuracy.
- Variable-duration bar planning, manual moods override, strict zero-based contiguous sections.
- API: POST /api/v1/analyze and POST /api/v1/blueprints.

## Validation
Run `pip install -e ".[dev]"`, then `pytest tests/phase_v2 -q` and
`ruff check src/wow tests/phase_v2`. Inspect /docs with uvicorn wow.api:app.

Phase 2 does NOT train an original emotion classifier. Manual mood correction
is core to the human-in-the-loop design. No GPU required.

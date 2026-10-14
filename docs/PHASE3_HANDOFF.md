# Phase 3 — Generation and rendering

- CPU-first generated four-role MIDI and WAV preview, saved durably in local jobs.sqlite3.
- `POST /api/v1/jobs` with blueprint: synchronous CPU job or pending manual Kaggle job.
- `GET /api/v1/jobs/{id}` returns persisted status and output names.
- Cloud import: place checked Kaggle files in `WOW_DATA_DIR/incoming/<safe_folder>/`,
  then `POST /api/v1/jobs/{id}/import` with folder_name.
- Import verifies manifest SHA-256, request ID, model name and MIDI structural validity.
- MIDI-to-audio is basic synthesized preview (NOT professional instrument sound).
- The cloud notebook smoke test still needs the user to run it on Kaggle.
- Real 12-bar pretrained-model assembly and automatic GPU dispatch require separate
  measured integration: this branch does not fabricate a complete neural model run.

Run `pip install -e ".[dev]"`, `pytest tests/phase_v2 -q`, `ruff check src/wow tests/phase_v2`
and inspect /docs. Never add credentials to Git.

# Phase 5: Reproducible objective evaluation + subjective feedback

Adds /api/v1/evaluations, /api/v1/feedback, /api/v1/feedback/summary/{id}.
Objective MIDI/audio metrics are computed from real files; perceived emotion
is intentionally null until listener ratings are collected. Ratings are
stored locally in SQLite, with no user identities collected.

Run CPU tests and Ruff, then follow docs/RESEARCH_PROTOCOL.md with blinded
listeners. No statistical superiority claims are made in this phase.

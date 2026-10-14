# Phase 4: Streamlit studio + immutable MIDI edit versions

Run two terminals, from a Python 3.11 virtual environment:

1. `pip install -e ".[dev,studio]"`
2. `python -m uvicorn wow.api:app --host 127.0.0.1 --port 8000`
3. `streamlit run studio_v2.py`

Local app: build and review a mood blueprint, generate deterministic four-track
MIDI and WAV, play audio, download MIDI/WAV, and edit one track/bar range. Earlier
versions remain accessible through the version selector (read-only 'undo').

MIDI events outside the edit are compared exactly after canonicalizing notes.
Editing within a bar is a deterministic operation, not a pretrained-model infill.
Cloud jobs require manual Kaggle artifact import. The old app is unchanged.

Verification: `pytest tests/phase_v2 -q`, `ruff check src/wow tests/phase_v2`
and a Windows browser/audio test before accepting the PR.

# Whispers of the Wires — AI-Based Music Composition System
**Mentor review draft · October 2026**

## Abstract
This individual project develops a controllable instrumental composition
prototype from descriptions of mood and situations. The application converts a
prompt into sequential emotional sections and a constrained music blueprint,
generates multitrack MIDI using a deterministic local baseline, synthesizes an
audio preview and supports targeted revisions. A Streamlit music dashboard
offers playback, saved compositions, playlists, variations, evaluations and
downloads. A separate Kaggle notebook is provided for inference with a
published MIDI-GPT checkpoint. The repository provides tests and transparent
metrics, but **pretrained AI-generated results and listener studies remain
unverified**, so no emotional accuracy or model superiority is asserted.

## Objectives
1. Convert mood/context prompts into editable musical stages.
2. Produce user-controlled instrumental compositions with melody, chords,
   bass and rhythm.
3. Show playback and composition history in a responsive Streamlit interface.
4. Preserve non-edited musical events through versioned bar/track edits.
5. Report measurable objective musical properties and collect listener feedback.

## System architecture
English prompt / context → reviewable emotion timeline → validated music
blueprint (tempo, key, genre, instruments, 4/4, sections) → local composer or
Kaggle MIDI-GPT adapter → multitrack MIDI → WAV preview → Streamlit dashboard
→ selective edits, playlist, evaluation and export. FastAPI provides typed
interfaces; SQLite stores jobs, library entries and feedback.

## Current implementation
- `src/wow/contracts.py`, `emotion.py`, `planning.py`: validated musical intent.
- `composer.py`, `generation.py`: deterministic CPU composition and jobs.
- `notebooks/kaggle/batch_generate.py`: unverified third-party GPU inference integration.
- `src/wow/editing.py`, `variations.py`: track/bar edits and alternate generations.
- `src/wow/library.py`: favorites, playlists, settings and saved library.
- `src/wow/evaluation.py`: structural/audio metrics and stored ratings.
- `studio_v2.py`: Streamlit Compose, albums, insights and help screens.
- `tests/phase_v2/`: automated CPU checks; `docs/MENTOR_DEMO.md`: reproducible demo.

## Testing and results
Actual CPU test logs and the latest GitHub Actions run are the authoritative
sources for pass counts. A local demo may report real note counts, file
durations and constraint scores. **No GPU timing, musical alignment,
human satisfaction, fine-tuned model results or cross-browser statistics are
available until experiments run.** A numerical goal listed in the planning
document is not a measured result.

## Limitations
Deterministic local MIDI generation does not constitute training an AI model;
preview instruments sound synthetic. The Kaggle inference adapter may require
compatibility changes. Genre and emotional mapping are heuristics, not proven
music psychology. Cloud batch execution is not low-latency streaming. Several
ambitious PDF features—crossfades, live EQ, collaborative filtering and
20-user load balancing—are outside the current single-developer MVP.

## Conclusion and mentor submission status
The project supports a preliminary functional dashboard-and-music demo.
It should **not** yet be represented as a fully evaluated, production-ready AI
composition system. The required remaining evidence is real Kaggle execution,
listener feedback, and device/browser acceptance. For the full source-to-code
audit, see `docs/REQUIREMENTS_TRACEABILITY.md`.

## References
MIDI-GPT: Pasquier et al. (2025), arXiv:2501.17011;
https://github.com/Metacreation-Lab/MIDI-GPT .
pretty_midi: https://github.com/craffel/pretty-midi .
Streamlit: https://docs.streamlit.io/ .
Uploaded project proposal, compressed timeline PDF and knowledge reference PDF.

# Mentor demo script — Whispers of the Wires

**Source branch:** `mentor-readiness-dashboard`.
**Python:** 3.11. **Run in two terminals.**

```bash
git clone https://github.com/shanmukhdatta/whispers_of_the_wires.git
cd whispers_of_the_wires
git checkout mentor-readiness-dashboard
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev,studio]"
pytest tests/phase_v2 -q
python scripts/local_smoke.py
```

For a one-command local launch, use `python run_studio.py`.

Terminal 1 (alternative):
```bash
python -m uvicorn wow.api:app --host 127.0.0.1 --port 8000
```
Terminal 2:
```bash
streamlit run studio_v2.py
```

Demo sequence:
1. Show blue dashboard tabs Compose / My Albums & Library / Insights / Help.
2. Prompt: "Nervous before an exam, then confident, finally relieved".
3. Choose 96 BPM, 4/4, cinematic, piano, 12 bars (30 seconds).
4. Generate a reviewed three-section musical blueprint.
5. Use **rule_based** and play the CPU-synthesized WAV.
6. Inspect waveform and objective structural/quality constraints.
7. Create a seeded variation, extend composition or edit harmony in bars 4–7.
8. Replay versions; export WAV, MIDI and project ZIP (MP3 if FFmpeg installed).
9. Favorite and add composition to a playlist; show saved history/analytics.
10. Explain the *separate* Kaggle third-party MIDI-GPT pathway. A real Kaggle
    run, exact checkpoint, logs and output are necessary before claiming neural
    AI generation was demonstrated.

Evidence to collect: GitHub Actions URL and pytest output, Windows screenshots,
audio file playback, version integrity, actual Kaggle run (if available), and
anonymous voluntary listener ratings (if collected). Do not invent evidence.

**No production guarantees:** Local single-user API, synthesized basic sound,
no guaranteed cloud GPU availability, not a commercial DAW or social streaming app.

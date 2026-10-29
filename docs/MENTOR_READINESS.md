# Mentor Submission Readiness — Whispers of the Wires

**Audit basis:** the submitted project statement/8-week plan, optimized 6-week implementation timeline, and technology reference guide. Checked against the source in this branch. The checkboxes in a project plan describe *targets*, not verified experimental results.

**Project status:** functional, offline-first composition demonstration; **not** a verified production-ready pretrained generative-music service. Never present deterministic MIDI composition as trained MIDI-GPT output.

## One-command demonstration

Use Python 3.11 and a clean environment:

```bash
git clone https://github.com/shanmukhdatta/whispers_of_the_wires.git
cd whispers_of_the_wires
git checkout phase-07-mentor-readiness
python -m pip install -e ".[dev,studio]"
python -m pytest tests/phase_v2 -q
python scripts/local_smoke.py
streamlit run mentor_dashboard.py
```

1. Start with "Nervous before my exam, then confident, finally relieved."
2. Set key, style, number of bars, seed, and tempo; choose **rule_based**.
3. Review the three emotional segments and generate a composition.
4. Play the audio, inspect waveform, download the WAV and four-track MIDI.
5. Apply a bar-restricted harmony edit, select the new version and listen.
6. Save the track as a favorite; reload the app and open it in **My music**.
7. Give listener feedback and examine objective metrics.
8. Export the project ZIP for a reproducible mentor demonstration.

The **midigpt** provider only creates a pending cloud job. A separate Kaggle run and validated artifact import are necessary for real pretrained-model output. For that, follow docs/CLOUD_WORKFLOW.md.

## Requirements traceability

| Document requirement | Status in this branch | Actual evidence / remaining gate |
|---|---|---|
| Emotion/context text inputs | Implemented baseline | Heuristic interpretation in wow.emotion; user-reviewable section table. No measured 85% recognition accuracy |
| Emotional journey and parameters | Implemented | Structured, validated bar sections and editable valence/arousal |
| Text-to-musical composition | Implemented **procedural** baseline | Seed-controlled four-track symbolic MIDI, key, tempo and five arrangement styles |
| Real pretrained model | **Not yet verified** | MIDI-GPT Kaggle adapter code exists but real GPU inference logs/outputs must be supplied |
| Audio output and playback | Implemented baseline | CPU waveform synthesizer, WAV files and Streamlit player. Sound is deliberately synthetic |
| Streamlit visual dashboard | Implemented for single-user demo | Blue gradient design, mood controls, library, player, waveform, metrics, feedback |
| Editing/variations | Implemented | New seed/take, lock-region MIDI edit, immutable stored versions, tests |
| WAV/MIDI/project export | Implemented | WAV, multitrack MIDI and integrity-manifest ZIP |
| Saved library/favorites | Implemented | SQLite-backed jobs and favorites; same workstation persists between app restarts |
| Music recommendation/personalization | Partial | Descriptive mood ratings after 3 ratings; **not** an online-trained personalization model |
| Quality scoring | Partial | Note counts, velocity, waveform peak/RMS and human survey storage; validated emotional match not established |
| Real-time streaming/playback controls | Partial | Playback of completed audio; no progressive model streaming, crossfade, live generation or web-scale queue |
| Genre/style transfer | Partial | Five local procedural arrangements; no learned style interpolation or neural style transfer |
| Multi-format production audio | Partial | WAV/MIDI, no verified MP3 export or studio-grade SoundFont/neural renderer |
| Multi-user hosting and load | Not verified | Single-user local workspace; 20+ concurrent users, <5s generation, uptime targets unmeasured |
| Evaluation/user satisfaction | Not verified | Framework exists; real consenting listener study, held-out prompts and statistics are required |
| CI/security/documentation | Partially verified | CPU tests/compilation/lint run on GitHub Actions; external deployment and security review not complete |

## Comparison with the project plans

The original 8-week plan requires model exploration, mood interpretation, music generation, Streamlit integration, rigorous testing, and final documentation. The code implements a demonstrated baseline workflow from input to editable MIDI/WAV and a UI. The 6-week accelerated timeline adds optional research/advanced features such as real-time streaming, continuous preference learning, multi-user load, music continuation, learned fine-tuning, user satisfaction targets and quality benchmarks. Those **cannot be marked completed simply because baseline source code exists**.

The reference guide lists SongComposer, MusicGen, MIDI-GPT, VAE/GAN and other architectures as candidates/knowledge resources. Their inclusion is **not evidence** that all models were integrated, trained or evaluated. The MIDI-GPT pathway was selected as an experimental candidate, with a transparent procedural fallback.

## Submission evidence still required

- [ ] Last GitHub Actions run on this exact branch is green, including Streamlit smoke test.
- [ ] Mentor opens the dashboard on the target Windows/laptop system and produces audible WAV and MIDI.
- [ ] A sample downloaded project ZIP is retained and its audio/MIDI playback is checked.
- [ ] Kaggle MIDI-GPT job with authentic checkpoint, logs, manifests and outputs succeeds; **or** clearly demonstrate the baseline and report GPU path as pending.
- [ ] Human listener ratings are collected and summarized; until then, omit any claims of emotional accuracy/85%+ satisfaction.
- [ ] Report actual CPU/GPU timing on the test hardware, not the ambitious plan's target timings.
- [ ] If public deployment is planned, complete multi-user privacy, authentication and performance checks; the current app is intended for a trusted, single-user local demo.
- [ ] Mentor handover includes README, research protocol, actual test output, known limitations, demo artifacts and third-party model license attributions.

## Honest demonstration statement

"Whispers of the Wires analyzes a short emotional scenario, proposes editable mood sections, and generates an original four-track MIDI arrangement with a synthesized WAV preview. It includes a local Streamlit studio, versioned edits, exports and evaluation tooling. The present live demo uses a reproducible rule-based composition baseline. A separate pretrained MIDI-GPT integration has been coded for Kaggle but has not yet been validated end-to-end on GPU; neural music quality and listener-alignment performance remain open evaluation tasks."

## Scope and licensing reminders

Do not promise a commercial music generator or copyright-free outputs. MIT covers repository-owned code only; music assets, pretrained model weights, datasets and SoundFonts have separate licenses. No model is trained by the demo itself. No continuous GPU server or paid inference is assumed.

# Whispers of the Wires 🎼

**An emotion-trajectory-guided, controllable AI-assisted music composition prototype**

[Requirements audit](docs/REQUIREMENTS_TRACEABILITY.md) ·
[Mentor demo guide](docs/MENTOR_DEMO.md) ·
[Project report](docs/FINAL_PROJECT_REPORT.md) ·
[Model choices](docs/MODEL_DECISIONS.md) ·
[Research protocol](docs/RESEARCH_PROTOCOL.md) ·
[PDF 30-day audit](docs/PDF_30_DAY_COVERAGE.md) ·
[User manual](docs/USER_MANUAL.md) ·
[Maintenance](docs/MAINTENANCE_AND_SUPPORT.md) ·
[Submission checklist](docs/FINAL_SUBMISSION_CHECKLIST.md) ·
[Classifier fine-tuning guide](docs/TRAINING_PROTOCOL.md)

> **Development status:** Dashboard + local four-track composition workflow implemented and checked in GitHub CI. Pretrained MIDI-GPT inference on Kaggle, musical quality studies, and cross-device usability are **not yet verified**. Do not interpret this repository as a validated production music generator.

## Project goal

Convert a text description of a mood, context, or situation into a sequence of
musical sections. Let the user review and customize the emotion trajectory,
compose original instrumental MIDI, hear a synthesized preview, edit specific
bars/tracks, and save songs in a personal dashboard.

Example: `Anxious before an exam, then confident, finally relieved`.

### Demonstrable features

- Streamlit music dashboard with **Compose**, **My Albums & Library**, **Insights**, and **Help** tabs.
- Mood/context text analysis with **editable** emotion stages, valence and arousal.
- Tempo, 4/4, key, genre, lead instrument and duration controls.
- CPU-only deterministic melody, harmony, bass and drum MIDI composition.
- Optional **MIDI-GPT yellow_medium** Kaggle batch integration (unverified until run).
- MIDI-to-WAV preview, waveform, **MIDI + WAV + project ZIP** export.
- MP3 export when **FFmpeg** is installed on the local machine.
- Targeted note editing, previous versions, new-seed variations and extensions.
- Saved compositions, favorites, playlists and locally stored listener ratings.
- Objective duration/note/audio checks, plus MFCC/spectral centroid/rolloff/chroma descriptors,
  distinct from human musical emotion scores.
- Context scenario inputs (activity, weather, time of day); no live sensors or weather data.
- Reversible MIDI quantization for authorized source files.
- Optional pretrained text-emotion classifier fine-tuning **code** with
  train/validation CSV leakage checks; no trained weights or research scores
  are bundled. The real experiment still needs approved data/GPU.
- Audio/MIDI dataset inspection (only use files you have the rights to use).

## Quick start (Python 3.11)

```bash
git clone https://github.com/shanmukhdatta/whispers_of_the_wires.git
cd whispers_of_the_wires
git checkout mentor-readiness-dashboard
python -m venv .venv
# Activate the environment: Windows -> .venv\Scripts\activate
#                         macOS/Linux -> source .venv/bin/activate
python -m pip install -e ".[dev,studio]"
python -m pytest tests/phase_v2 -q
python run_studio.py
```

Open **http://localhost:8501** for the composition dashboard.
Open **http://127.0.0.1:8000/docs** for the documented FastAPI contract.
The launcher runs both local processes; it does not publish the API on the internet.

Alternative two-terminal start:
```bash
python -m uvicorn wow.api:app --host 127.0.0.1 --port 8000
# In a second terminal:
streamlit run studio_v2.py
```

**Fast mentor demo:** select `rule_based`, plan and edit three emotions,
generate 12 bars, play the WAV, create a variation, open the library and save
favorite/playlist, then export MIDI and ZIP. This is a working **symbolic
baseline**, not the trained neural model.

## AI generation on Kaggle

The optional provider `midigpt` creates an **awaiting_cloud** job.
The Kaggle CLI integration can prepare and submit a **private** notebook,
retrieve generated outputs and import checksummed MIDI back into the project.

Read [Cloud workflow](docs/CLOUD_WORKFLOW.md) before submitting.

**Limitations:** Free cloud GPUs are intermittent. The chosen yellow checkpoint
has 4/8-bar contexts, so longer pieces require segment assembly and quality
checks. A real Kaggle run, model version and output must be retained as evidence;
no always-on low-latency service is promised.

## Repository layout

```text
src/wow/
  api.py              FastAPI server and validated requests
  contracts.py        Versioned music blueprint
  emotion.py          Text mood suggestions
  planning.py         Section and arrangement plan
  composer.py         Deterministic four-track MIDI baseline
  generation.py       Local jobs and cloud import
  cloud_jobs.py       Opt-in private Kaggle CLI adapter
  rendering.py        Basic waveform audio synthesizer
  editing.py          Bar/track editing with locked-event checks
  variations.py       Seed variations and extensions
  evaluation.py       Objective metrics and listener rating storage
  audio_features.py   Spectral descriptors, MFCC, symbolic chroma
  midi_preprocess.py  Quantization without overwriting source
  context.py          Explicit and text-mentioned activity/weather/time
  library.py          Favorites, playlists, preferences and saved songs
  data_pipeline.py    Authorized MIDI/WAV/FLAC inspection
  audio_export.py     FFmpeg-based MP3 export
studio_v2.py          Streamlit music dashboard
run_studio.py         One-command local dashboard launcher
notebooks/kaggle/     Pretrained model integration candidates
scripts/             Reproducible CPU demo and data checks
tests/phase_v2/       Unit/integration tests
docs/                 Mentor report, model decisions, audit, demo guide
```

Legacy `app/main.py` and `run.py` are preserved for comparison but are **not
the V2 composition dashboard entry points**. Use `run_studio.py` for the
mentor-facing app.

## Evaluation integrity

GitHub CI checks imports/compilation, Python dependencies, 37 automated CPU
tests, local music generation and a factual mentor evidence script. Test counts
may change as the project evolves; use the latest GitHub Actions run.

**No claims are made** of measured 85% mood accuracy, five-second AI music
generation, 20+ concurrent users, 99.5% uptime, production readiness or model
superiority. Those numerical targets appear in the compressed six-week planning
PDF, not in reproducible experiment results.

## Original plan versus prototype

The uploaded primary DOCX specifies five modules and an eight-week schedule:
model exploration, mood/context interpretation, music generation, Streamlit UI,
and testing/documentation. The additional PDF expands the idea to
fine-tuning, social streaming, complex audio controls, scalability and
quantitative targets. This repository implements a defensible solo-developer
academic prototype; the [audit matrix](docs/REQUIREMENTS_TRACEABILITY.md)
identifies features still awaiting experiments or out of core MVP scope.

## Licensing and acknowledgments

Project source code follows this repository's `LICENSE`.
Third-party **model weights have separate terms**: MIDI-GPT pretrained
checkpoints are noncommercial research/education assets, not unrestricted
MIT-licensed content. Dataset, SoundFont and music copyrights must also be
respected. No copyrighted artist albums or songs are bundled with the
new dashboard.

MIDI-GPT: [research repository](https://github.com/Metacreation-Lab/MIDI-GPT) ·
[paper](https://arxiv.org/abs/2501.17011) ·
[Streamlit](https://docs.streamlit.io/) ·
[pretty_midi](https://github.com/craffel/pretty-midi).

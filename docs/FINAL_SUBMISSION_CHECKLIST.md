# Mentor handoff: no unsupported claims checklist

## Files to show your mentor
- Source: `mentor-readiness-dashboard` branch and exact Git commit SHA.
- User-facing Streamlit: `studio_v2.py`; single command: `python run_studio.py`.
- Research source docs: original 8-week DOCX; six-week PDF; technology guide.
- [Day-by-day PDF audit](PDF_30_DAY_COVERAGE.md).
- [Requirements traceability](REQUIREMENTS_TRACEABILITY.md).
- [Architecture/model decisions](MODEL_DECISIONS.md).
- [Project report](FINAL_PROJECT_REPORT.md).
- [Training protocol](TRAINING_PROTOCOL.md).
- [User manual](USER_MANUAL.md).
- [Maintenance/support](MAINTENANCE_AND_SUPPORT.md).
- [Demo guide](MENTOR_DEMO.md).

## Automated evidence
- [ ] Green GitHub Actions for final exact commit.
- [ ] Passing CPU unit/integration suite.
- [x] Automated local smoke and factual mentor evidence generation on GitHub Actions.
- [ ] Download and listen to the generated WAV from the most recent Actions artifact.
- [x] CPU timing script runs inside CI and uploads its actual JSON timings.

## Manual evidence still required
- [ ] Screen recording of Compose -> WAV playback -> edit -> Library.
- [ ] Windows and mobile/browser player tests; automated initial Streamlit render is covered in CI.
- [ ] Successful Kaggle MIDI-GPT pretrained run with actual output and timing.
- [ ] Real, permissioned text-label train/validation set and optional fine-tune
      output if training is within the agreed mentor scope.
- [ ] Blind listener mood/coherence ratings and aggregate statistics.
- [ ] Mentor approval of any narrowed production scope.

**Submission wording:** "Source code and local prototype built; final
model/user evaluation is pending." Do not label an unrun script as a
completed experiment, and do not claim the PDF's 85%, <5s and uptime goals
without data.

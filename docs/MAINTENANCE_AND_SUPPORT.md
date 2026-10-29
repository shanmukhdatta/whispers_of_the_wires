# Operational maintenance, privacy and recovery

## Supported setup
- Local Python 3.11, Streamlit and loopback FastAPI.
- User-owned music inputs/outputs stored under `.wow_workspace/`.
- SQLite storage for composition jobs, playlists and optional ratings.
- Kaggle CLI and GPU are **optional** for the pretrained symbolic generator.

## Safe startup / failure handling
- Run `python run_studio.py` or separate `uvicorn` + Streamlit terminals.
- Health endpoint: `GET http://127.0.0.1:8000/health`.
- API schema: `GET /openapi.json`; examples in `/docs`.
- Start with `rule_based` to distinguish a local bug from cloud model failure.
- If MP3 is unavailable, verify FFmpeg is on PATH; WAV/MIDI do not require it.
- If a Kaggle job is pending, retain the UUID and notebook run URL; inspect
  the Kaggle error log before any retry. Model output must pass checksums.

## Backup/recovery
1. Shut down the FastAPI and Streamlit processes.
2. Make an offline copy of the complete `.wow_workspace` directory,
   including `jobs.sqlite3`, `library.sqlite3`, `feedback.sqlite3` and
   `artifacts/`. A database without associated assets is not a full backup.
3. Restore the full directory on the same application version, after the
   service is stopped, and verify `GET /api/v1/library` and a saved WAV.
4. Keep Kaggle credentials **outside Git** and never archive credential files.

No automated backup schedule or production disaster recovery exercise has
been tested, so do not claim one exists.

## Security / privacy
- Bind the API to `127.0.0.1`. No public-authenticated multiuser web server
  exists and the local API must not be exposed directly to the internet.
- Do not commit private prompt datasets, participant ratings, copyrighted
  music recordings, secret tokens or proprietary model files.
- Separate user-entered emotional mood text from clinical/health claims.
- Collect anonymous evaluation feedback with consent; do not ask testers to
  submit personal secrets.
- Feature data is interpreted descriptively; no mood accuracy metrics exist.

## Release checks
```bash
python -m pytest tests/phase_v2 -q
python scripts/local_smoke.py
python scripts/mentor_demo.py --output .wow_workspace/mentor
python scripts/benchmark_cpu.py --output .wow_workspace/cpu_benchmark.json
```
Retain the exact GitHub Actions URL and head SHA. Document exceptions from
manual Windows/mobile review and real Kaggle execution before final sign-off.

## Future development
Prioritize, in order: actual MIDI-GPT GPU run and checkpoint provenance,
rights-cleared labeled-data fine-tuning experiments, blinded listener
evaluation, audio quality/synth improvement, responsive/browser QA, then
security and scalability if moving beyond a single-user academic demo.

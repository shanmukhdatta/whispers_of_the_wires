# Phase 6 — hardening and final candidate

Changes:
- SHA256 artifact metadata validation rejects malformed JSON without a cryptic crash.
- Final CPU CI checks: dependencies, compileall, tests and Ruff.
- Reproducible CPU end-to-end smoke script.
- Candidate Kaggle batch generator loops over four-bar contexts to cover planned sections.
- Documented model and license limitations, manual cloud workflow and user acceptance gates.
- Existing legacy Streamlit app is preserved; new studio is separate.

## CPU acceptance
`pip install -e ".[dev,studio]"`
`pytest tests/phase_v2 -q`
`ruff check src/wow tests/phase_v2`
`python scripts/local_smoke.py` (install package first)
`uvicorn wow.api:app --host 127.0.0.1 --port 8000`
`streamlit run studio_v2.py`

## GPU acceptance
Follow docs/CLOUD_WORKFLOW.md and retain Kaggle notebook URL, execution
logs, exact checkpoint revision, generated MIDI and manifest. GPU inference,
musical quality, public hosting and human emotion ratings remain unverified.

Do not merge stacked PRs without reviewing each and verifying the last
green CI run. Do not claim 100% production readiness from passing CPU CI.

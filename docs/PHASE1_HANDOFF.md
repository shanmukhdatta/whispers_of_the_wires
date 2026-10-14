# Phase 1 handoff

This branch adds a parallel `wow` Python package, leaving the legacy Streamlit
entrypoint on `main` untouched.

## CPU verification (Python 3.11)
1. Create and activate a fresh virtual environment.
2. Run `python -m pip install -e ".[dev]"`.
3. Run `python -m pytest tests/phase_v2 -q`.
4. Run `python -m uvicorn wow.api:app --reload` and open `http://127.0.0.1:8000/docs`.
5. Generate a MIDI with:
   `python -c "from wow.contracts import default_blueprint; from wow.composer import compose_rule_based,save_midi; save_midi(compose_rule_based(default_blueprint('demo')), 'demo.mid')"`
   (pass a pathlib.Path instead of the string on strict platforms).

## Cloud verification
Read `notebooks/kaggle/README.md` and execute the smoke test in Kaggle.
GPU loading, inference, costs and output have NOT been verified from this GitHub
commit. Report actual run ID, device, duration, dependency errors and MIDI output.

## Caveats
A musical emotion classifier, selective editing, user accounts, automatic Kaggle
dispatch, and pretrained GPU generation inside the local application are NOT
included in Phase 1. The rules-based result is a transparent baseline.

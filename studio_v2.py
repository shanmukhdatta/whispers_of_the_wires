"""Composition-first Streamlit studio. Launch the API separately via uvicorn."""
from __future__ import annotations

import copy
import io
import json
import os

import numpy as np
import pandas as pd
import requests
import soundfile as sf
import streamlit as st

API = os.environ.get("WOW_API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Whispers of the Wires Studio", page_icon="🎼", layout="wide")
st.title("🎼 Whispers of the Wires — Composition Studio")
st.caption("Review your emotion timeline, generate multitrack MIDI, and revise selected bars.")


def call(method: str, path: str, *, timeout: int = 120, **kwargs):
    """Local-only API client; report actual failures."""
    response = requests.request(method, f"{API}{path}", timeout=timeout, **kwargs)
    response.raise_for_status()
    return response


prompt = st.text_area(
    "What emotional story should the instrumental composition tell?",
    "Nervous before an exam, then confident, finally relieved",
)
c1, c2, c3 = st.columns(3)
with c1:
    tempo = st.slider("Tempo (BPM)", 60, 160, 96)
with c2:
    bars = st.select_slider("Number of bars", [6, 9, 12, 16, 24], value=12)
with c3:
    provider = st.selectbox("Generation backend", ["rule_based", "midigpt"])
manual_moods = st.text_input(
    "Override the stages (optional, comma-separated)", help="Example: nervous, confident, relieved"
)
if st.button("Analyze and create plan", type="primary", use_container_width=True):
    try:
        args = {"prompt": prompt, "tempo_bpm": tempo, "total_bars": bars}
        if manual_moods.strip():
            args["moods"] = [word.strip() for word in manual_moods.split(",") if word.strip()]
        st.session_state["blueprint"] = call(
            "POST", "/api/v1/blueprints", json=args, timeout=20
        ).json()
    except (requests.RequestException, ValueError) as exc:
        st.error(f"Planning failed: {exc}")

if "blueprint" in st.session_state:
    blueprint = st.session_state["blueprint"]
    st.subheader("Edit your emotional journey")
    st.caption("Edit mood, valence and arousal. Bar boundaries and IDs are locked.")
    frame = pd.DataFrame(blueprint["sections"])
    selected = st.data_editor(
        frame,
        hide_index=True,
        num_rows="fixed",
        disabled=["id", "start_bar", "bar_count"],
        column_config={
            "valence": st.column_config.NumberColumn(
                "Valence (-1 to +1)", min_value=-1.0, max_value=1.0, step=0.1
            ),
            "arousal": st.column_config.NumberColumn(
                "Arousal (-1 to +1)", min_value=-1.0, max_value=1.0, step=0.1
            ),
        },
        use_container_width=True,
        key=f"section_editor_{blueprint['request_id']}",
    )
    candidate = copy.deepcopy(blueprint)
    candidate["sections"] = selected.to_dict(orient="records")
    candidate["generation"]["provider"] = provider
    candidate["generation"]["checkpoint"] = (
        "yellow_medium" if provider == "midigpt" else "rule_based_v1"
    )
    st.caption("Generator 'rule_based' works without GPU. MIDI-GPT needs a Kaggle run.")
    if st.button("Generate with this reviewed blueprint", use_container_width=True):
        try:
            result = call("POST", "/api/v1/jobs", json=candidate).json()
            st.session_state["job_id"] = result["job_id"]
            st.session_state["active_blueprint"] = candidate
            st.success(f"Created job {result['job_id']} — {result['state']}")
        except requests.RequestException as exc:
            st.error(f"Generation failed: {exc}")

if "job_id" in st.session_state:
    job_id = st.session_state["job_id"]
    st.subheader("Your composition")
    if st.button("Refresh job status"):
        st.rerun()
    try:
        job = call("GET", f"/api/v1/jobs/{job_id}", timeout=20).json()
        st.write(f"**Job status:** {job['state']} | **Provider:** {job['provider']}")
        if job["state"] == "awaiting_cloud":
            st.info("A real MIDI-GPT composition must be generated on Kaggle and imported.")
            bp_json = json.dumps(st.session_state.get("active_blueprint", {}), indent=2)
            st.download_button(
                "Download this job's blueprint", bp_json, file_name="blueprint.json",
                mime="application/json",
            )
            st.code(
                "python scripts/kaggle_job.py prepare <JOB_ID> --username <KAGGLE_USERNAME>\n"
                "python scripts/kaggle_job.py push <JOB_ID>\n"
                "python scripts/kaggle_job.py status <USERNAME>/<KERNEL_SLUG>\n"
                "python scripts/kaggle_job.py collect <JOB_ID> <USERNAME>/<KERNEL_SLUG>"
            )
            st.caption("Replace the placeholders; see docs/CLOUD_WORKFLOW.md for full details.")
        elif job["state"] == "completed":
            metadata = call("GET", f"/api/v1/compositions/{job_id}", timeout=20).json()
            history = metadata["versions"]
            version = st.selectbox("Composition version", history, index=len(history) - 1)
            def fetch_asset(filename: str) -> bytes:
                return call(
                    "GET", f"/api/v1/compositions/{job_id}/assets/{filename}",
                    params={"version": version}, timeout=40,
                ).content
            wav = fetch_asset("composition.wav")
            st.audio(wav, format="audio/wav")
            array, rate = sf.read(io.BytesIO(wav), always_2d=True)
            series = np.mean(array, axis=1)
            skip = max(1, len(series) // 1500)
            waveform = pd.DataFrame({
                "second": np.arange(0, len(series), skip) / rate,
                "amplitude": series[::skip],
            })
            st.line_chart(waveform, x="second", y="amplitude")
            left, right, third = st.columns(3)
            with left:
                st.download_button("Download WAV", wav, file_name=f"wow-v{version}.wav")
            with right:
                st.download_button(
                    "Download MIDI", fetch_asset("composition.mid"),
                    file_name=f"wow-v{version}.mid",
                )
            with third:
                if st.button("Prepare full project ZIP"):
                    archive = call(
                        "GET", f"/api/v1/compositions/{job_id}/export",
                        params={"version": version}, timeout=60,
                    ).content
                    st.session_state["project_archive"] = (version, archive)
            if "project_archive" in st.session_state:
                archived_version, data = st.session_state["project_archive"]
                if archived_version == version:
                    st.download_button(
                        "Save complete project ZIP", data,
                        file_name=f"whispers-project-v{version}.zip",
                    )
            report = call(
                "POST", "/api/v1/evaluations",
                json={"composition_id": job_id, "version": version},
            ).json()
            with st.expander("Measured music metrics"):
                st.json(report)
            st.subheader("Help improve future compositions")
            with st.form("feedback_form"):
                mood_section = st.selectbox(
                    "Which emotional section?", [s["id"] for s in
                                                 st.session_state["active_blueprint"]["sections"]]
                )
                mood_match = st.slider("Emotion match", 1, 5, 3)
                musicality = st.slider("Musical coherence", 1, 5, 3)
                comments = st.text_area("Optional comments", max_chars=500)
                submitted = st.form_submit_button("Save listener feedback")
            if submitted:
                response = call(
                    "POST", "/api/v1/feedback",
                    json={"composition_id": job_id, "version": version,
                          "section_id": mood_section, "mood_match": mood_match,
                          "musical_coherence": musicality, "comments": comments},
                ).json()
                if response.get("stored"):
                    st.success("Saved. Ratings are not claims of model accuracy.")
            preference = call("GET", "/api/v1/preferences").json()
            if preference.get("sufficient_data"):
                st.caption("Past mood preferences (descriptive, not model-trained)")
                st.dataframe(preference["recommendations"], hide_index=True)
            st.subheader("Selective bar-level MIDI editing")
            active_bp = st.session_state.get("active_blueprint", blueprint)
            maximum = int(active_bp["total_bars"])
            tracks = [t["id"] for t in active_bp["tracks"]]
            track = st.selectbox("Track to modify", tracks)
            start = st.number_input(
                "First bar (0-indexed)", min_value=0, max_value=maximum - 1,
                value=min(4, maximum - 1),
            )
            end = st.number_input(
                "End bar (exclusive)", min_value=int(start) + 1,
                max_value=maximum, value=min(maximum, int(start) + 4),
            )
            operation = st.selectbox(
                "Edit action", ["more_energy", "less_dense", "transpose_up"]
            )
            if st.button("Create a new edited version"):
                edit = {
                    "base_version": metadata["latest"], "track_ids": [track],
                    "start_bar": int(start), "end_bar_exclusive": int(end),
                    "operation": operation,
                }
                response = call(
                    "POST", f"/api/v1/compositions/{job_id}/edits", json=edit
                ).json()
                st.success(f"Version {response['version']} saved; refresh to hear it.")
        else:
            st.warning(json.dumps(job.get("data", {}), indent=2))
    except (requests.RequestException, ValueError, sf.LibsndfileError) as exc:
        st.error(f"Unable to load composition: {exc}")

"""New standalone Streamlit studio; existing legacy app/main.py is untouched."""
from __future__ import annotations

import os

import requests
import streamlit as st

API = os.environ.get("WOW_API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Whispers of the Wires Studio", page_icon="🎼",
                   layout="wide")
st.title("🎼 Whispers of the Wires — Composition Studio")
st.caption("Prototype: controllable symbolic MIDI + CPU WAV preview. Cloud GPU runs are manual.")
prompt = st.text_area("Describe the emotional journey",
                      "Nervous before an exam, then confident, finally relieved")
col1, col2, col3 = st.columns(3)
with col1:
    tempo = st.slider("Tempo (BPM)", 60, 160, 96)
with col2:
    bars = st.select_slider("Length (bars)", [6, 9, 12, 16, 24], value=12)
with col3:
    provider = st.selectbox("Generator", ["rule_based", "midigpt"])
mood_text = st.text_input("Optional ordered moods (comma-separated)",
                          help="Correct the emotion timeline before generation")
if st.button("Plan music", use_container_width=True):
    try:
        request = {"prompt": prompt, "tempo_bpm": tempo, "total_bars": bars}
        if mood_text.strip():
            request["moods"] = [v.strip() for v in mood_text.split(",") if v.strip()]
        response = requests.post(f"{API}/api/v1/blueprints", json=request, timeout=20)
        response.raise_for_status()
        st.session_state["blueprint"] = response.json()
    except (requests.RequestException, ValueError) as exc:
        st.error(f"Planning failed: {exc}")

if "blueprint" in st.session_state:
    blueprint = st.session_state["blueprint"]
    st.subheader("Review and adjust your music blueprint")
    st.json(blueprint, expanded=False)
    st.caption("Mood interpretations are suggestions. Update the mood field and regenerate plan.")
    if st.button("Generate composition", type="primary"):
        try:
            blueprint["generation"]["provider"] = provider
            blueprint["generation"]["checkpoint"] = (
                "yellow_medium" if provider == "midigpt" else "rule_based_v1"
            )
            response = requests.post(f"{API}/api/v1/jobs", json=blueprint, timeout=120)
            response.raise_for_status()
            result = response.json()
            st.session_state["job_id"] = result["job_id"]
            st.info(f"Job status: {result['state']}")
        except requests.RequestException as exc:
            st.error(f"Generation failed: {exc}")

if "job_id" in st.session_state:
    job_id = st.session_state["job_id"]
    try:
        response = requests.get(f"{API}/api/v1/compositions/{job_id}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            version = st.selectbox("Listen to version", data["versions"],
                                   index=len(data["versions"]) - 1)
            def asset(name: str) -> bytes:
                result = requests.get(
                    f"{API}/api/v1/compositions/{job_id}/assets/{name}",
                    params={"version": version}, timeout=45,
                )
                result.raise_for_status()
                return result.content
            wav = asset("composition.wav")
            st.audio(wav, format="audio/wav")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Download WAV", wav, file_name=f"wow-v{version}.wav")
            with c2:
                st.download_button("Download MIDI", asset("composition.mid"),
                                   file_name=f"wow-v{version}.mid")
            st.subheader("Selective MIDI editing")
            track = st.selectbox("Track", ["melody", "harmony", "bass", "drums"])
            start = st.number_input("First bar (zero-indexed)", 0, bars - 1, 4)
            end = st.number_input("End bar (exclusive)", int(start) + 1, bars, 8)
            action = st.selectbox("Edit", ["more_energy", "less_dense", "transpose_up"])
            if st.button("Apply selected edit"):
                request = {
                    "base_version": data["latest"],
                    "track_ids": [track], "start_bar": int(start),
                    "end_bar_exclusive": int(end), "operation": action,
                }
                result = requests.post(f"{API}/api/v1/compositions/{job_id}/edits",
                                       json=request, timeout=120)
                if result.ok:
                    st.success(f"Created version {result.json()['version']}. Reload to listen.")
                else:
                    st.error(result.text)
        else:
            st.info("Composition is not ready. Cloud jobs need a completed Kaggle import.")
    except requests.RequestException as exc:
        st.error(f"Backend unavailable: {exc}")

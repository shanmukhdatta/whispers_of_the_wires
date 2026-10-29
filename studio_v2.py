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
st.markdown("""<style>
.stApp {background: linear-gradient(125deg, #070f25 0%, #102c5d 52%, #09182d 100%);
color: #edf3ff;}
div[data-testid="stVerticalBlockBorderWrapper"] {background: rgba(10,21,43,.65);}
div[data-testid="stMetric"] {background:rgba(35,74,139,.3);padding:12px;border-radius:12px;}
.stButton>button {border-radius:10px;}
section[data-testid="stSidebar"] {background: #0a1935;}
</style>""", unsafe_allow_html=True)
st.title("🎼 WHISPERS OF THE WIRES")
st.caption("Compose original music from a story, preview audio, and keep your own album.")
tab_create, tab_library, tab_insights, tab_guide = st.tabs(
    ["✦ Compose", "♫ My Albums & Library", "◉ Insights", "ⓘ Project & Help"]
)


def call(method: str, path: str, *, timeout: int = 120, **kwargs):
    """Local-only API client; report actual failures."""
    response = requests.request(method, f"{API}{path}", timeout=timeout, **kwargs)
    response.raise_for_status()
    return response


with tab_create:
    PRESETS = {
        "Write my own story": "Nervous before an exam, then confident, finally relieved",
        "Peaceful morning": "peaceful morning, then joyful, finally relaxed",
        "Study motivation": "anxious before studying, then determined, finally confident",
        "Rainy reflection": "sad rainy evening, then peaceful, finally hopeful",
        "Celebration": "excited for a celebration, then joyful, finally relieved",
    }
    preset = st.selectbox("Story inspiration", list(PRESETS), key="preset_choice")
    prompt = st.text_area(
        "Describe the mood, situation or emotional journey",
        value=PRESETS[preset], key=f"prompt_{preset}",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        tempo = st.slider("Tempo (BPM)", 60, 160, 96)
    with c2:
        bars = st.select_slider("Number of bars", [6, 9, 12, 16, 24], value=12)
    with c3:
        provider = st.selectbox("Generation backend", ["rule_based", "midigpt"])
    g1, g2, g3 = st.columns(3)
    with g1:
        genre = st.selectbox(
            "Music style", ["cinematic", "ambient", "classical", "electronic", "jazz"]
        )
    with g2:
        music_key = st.selectbox("Musical key", ["C_major", "G_major", "F_major", "A_minor"])
    with g3:
        melody_program = st.selectbox(
            "Lead instrument (General MIDI)",
            ["Piano", "Electric piano", "Guitar", "Strings", "Synth lead"],
        )
    PROGRAMS = {"Piano": 0, "Electric piano": 4, "Guitar": 24,
                "Strings": 48, "Synth lead": 80}
    manual_moods = st.text_input(
        "Override the stages (optional, comma-separated)", help="Example: nervous, confident, relieved"
    )
    if st.button("Analyze and create plan", type="primary", use_container_width=True):
        try:
            args = {"prompt": prompt, "tempo_bpm": tempo, "total_bars": bars,
                    "key": music_key, "genre": genre,
                    "instrument_programs": {"melody": PROGRAMS[melody_program]}}
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
                try:
                mp3 = call(
                    "GET", f"/api/v1/compositions/{job_id}/assets/composition.mp3",
                    params={"version": version}, timeout=60,
                ).content
                st.download_button("Download MP3 (FFmpeg)", mp3,
                                   file_name=f"wow-v{version}.mp3")
            except requests.RequestException:
                st.caption("MP3 needs FFmpeg installed locally; WAV and MIDI remain available.")
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
                                                     (st.session_state.get("active_blueprint") or st.session_state.get("blueprint"))["sections"]]
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
                st.subheader("Create a fresh variation or extension")
            variable_seed = st.number_input(
                "New random seed", min_value=0, max_value=4294967295,
                value=2027, step=1, key="variation_seed"
            )
            extension = st.selectbox("Add bars at the end", [0, 4, 8, 12],
                                     key="extend_bars_choice")
            if st.button("Generate new variation"):
                response = call(
                    "POST", f"/api/v1/compositions/{job_id}/variations",
                    json={"seed": int(variable_seed), "extend_bars": extension},
                ).json()
                st.session_state["job_id"] = response["job_id"]
                st.info("New variation requested. Refresh to listen.")
            st.subheader("Selective bar-level MIDI editing")
                active_bp = st.session_state.get("active_blueprint") or st.session_state.get("blueprint")
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

with tab_library:
    st.subheader("My albums & saved compositions")
    st.caption("Your generated compositions, not a catalog of copyrighted music.")
    if st.button("Refresh my library", key="refresh_library"):
        st.rerun()
    try:
        collection = call("GET", "/api/v1/library", params={"limit": 100}, timeout=20).json()
        tracks = [song for song in collection["items"] if song["state"] == "completed"]
        favorites = [song for song in tracks if song["favorite"]]
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Compositions", len(tracks))
        col_b.metric("Favorites", len(favorites))
        col_c.metric("All jobs", collection["count"])
        if not tracks:
            st.info("Your album is empty. Go to Compose and generate the first track.")
        else:
            st.write("### Featured compositions")
            labels = {
                s["job_id"]: (
                    f"{'★ ' if s['favorite'] else ''}{s['prompt'][:65]} "
                    f"· {s['genre']} · {s['tempo_bpm']} BPM"
                )
                for s in tracks
            }
            selected_id = st.selectbox(
                "Choose a saved composition", list(labels),
                format_func=lambda sid: labels[sid], key="library_track_selector",
            )
            chosen = next(s for s in tracks if s["job_id"] == selected_id)
            st.write(f"**Story:** {chosen['prompt']}")
            st.caption(
                f"Style: {chosen['genre']} · Moods: {', '.join(chosen['moods'])}"
            )
            preview = call(
                "GET", f"/api/v1/compositions/{selected_id}/assets/composition.wav",
                timeout=30,
            ).content
            st.audio(preview, format="audio/wav")
            left, middle, right = st.columns(3)
            with left:
                if st.button(
                    "Remove favorite" if chosen["favorite"] else "☆ Add to favorites",
                    key=f"favorite_{selected_id}",
                ):
                    call(
                        "PUT", f"/api/v1/library/{selected_id}/favorite",
                        json={"favorite": not chosen["favorite"]},
                    )
                    st.rerun()
            with middle:
                st.download_button(
                    "Save WAV", preview, file_name=f"{selected_id[:8]}.wav"
                )
            with right:
                mid = call(
                    "GET", f"/api/v1/compositions/{selected_id}/assets/composition.mid"
                ).content
                st.download_button(
                    "Save MIDI", mid, file_name=f"{selected_id[:8]}.mid"
                )
            if st.button("Open in composer", key="open_track"):
                st.session_state["job_id"] = selected_id
                st.session_state["active_blueprint"] = call(
                    "GET", f"/api/v1/compositions/{selected_id}/blueprint"
                ).json()
                st.info("Selected: switch to the Compose tab to edit.")
            st.write("### Playlist management")
            with st.form("playlist_form"):
                playlist_name = st.text_input("New playlist name", max_chars=80)
                created = st.form_submit_button("Create playlist")
                if created and playlist_name.strip():
                    call("POST", "/api/v1/playlists", json={"name": playlist_name})
                    st.success("Playlist created")
            playlists = call("GET", "/api/v1/playlists").json()["items"]
            if playlists:
                playlist_id = st.selectbox(
                    "Select a playlist", [p["id"] for p in playlists],
                    format_func=lambda pid: next(p["name"] for p in playlists
                                                 if p["id"] == pid),
                )
                if st.button("Add selected music to playlist"):
                    call(
                        "POST", f"/api/v1/playlists/{playlist_id}/items",
                        json={"composition_id": selected_id},
                    )
                    st.success("Saved to playlist")
                active = next(p for p in playlists if p["id"] == playlist_id)
                st.caption(f"Playlist contains {len(active['items'])} compositions")
                for item in active["items"]:
                    st.text(labels.get(item, item[:8]))
            st.write("### Complete composition history")
            st.dataframe(
                [{"Story": x["prompt"], "Style": x["genre"],
                  "Tempo": x["tempo_bpm"], "Status": x["state"],
                  "Favorite": "★" if x["favorite"] else ""}
                 for x in collection["items"]],
                hide_index=True, use_container_width=True,
            )
    except (requests.RequestException, ValueError) as exc:
        st.error(f"Library unavailable: {exc}")

with tab_insights:
    st.subheader("Music & usage insights")
    st.caption("Numbers below are calculated from saved jobs and listener ratings.")
    try:
        collection = call("GET", "/api/v1/library").json()["items"]
        completed = [item for item in collection if item["state"] == "completed"]
        if completed:
            by_genre = pd.Series([item["genre"] for item in completed]).value_counts()
            st.bar_chart(by_genre, x_label="Music style", y_label="Compositions")
            st.dataframe(
                [{"Composition": item["prompt"][:50], "Provider": item["provider"],
                  "Moods": " → ".join(item["moods"])}
                 for item in completed],
                hide_index=True, use_container_width=True,
            )
        else:
            st.info("Generate some compositions to see metrics.")
        prefs = call("GET", "/api/v1/preferences").json()
        if prefs["sufficient_data"]:
            st.write("### Feedback-derived preferences")
            st.dataframe(prefs["recommendations"], hide_index=True)
        else:
            st.info("Mood preference summaries require at least three ratings per mood.")
        st.info(
            "These metrics describe your local use. They do not establish that "
            "the AI generated music matches the intended emotion."
        )
    except requests.RequestException as exc:
        st.error(f"Unable to load analytics: {exc}")

with tab_guide:
    st.subheader("How to use")
    st.markdown("""
    1. **Compose:** Describe your situation, choose instruments/style and review
       your three-stage emotional trajectory.
    2. **Generate:** The CPU rules-based composer works immediately; MIDI-GPT
       requires a Kaggle cloud model run.
    3. **Listen and revise:** Play the WAV, inspect metrics, and change selected
       MIDI bars while preserving other parts.
    4. **My Albums & Library:** Mark favorites, organize your generated tracks
       into playlists and download WAV/MIDI.
    5. **Evaluation:** Rate emotional alignment and coherence. These ratings
       remain separate from mathematical note-density metrics.
    """)
    st.warning(
        "The AI checkpoint has not yet been demonstrated on Kaggle in this "
        "repository's CI. The preview audio is synthesized, not professionally "
        "recorded. Never claim unmeasured accuracy or generation speed."
    )

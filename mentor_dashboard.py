"""Single-command mentor demo for Whispers of the Wires.

Run: streamlit run mentor_dashboard.py
The default composer is a deterministic symbolic baseline, NOT a pretrained model.
MIDI-GPT requires an independently verified Kaggle GPU job.
"""
from __future__ import annotations

import copy
import os
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
import streamlit as st
from pydantic import ValidationError

from wow.contracts import MusicBlueprint
from wow.editing import EditRequest, create_edit_version, version_directory, versions
from wow.evaluation import FeedbackStore, ListenerRating, evaluate_files
from wow.generation import GenerationService
from wow.planning import PlanningRequest, build_blueprint
from wow.preferences import recommend_moods
from wow.project_archive import build_project_archive

st.set_page_config(
    page_title="Whispers of the Wires | Music Studio",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
<style>
.stApp {
  background: radial-gradient(ellipse at 85% 0%, #102e76 0%, #081735 36%, #080d1d 72%);
  color: #f1f5fc;
}
[data-testid="stSidebar"] {background: #081123; border-right: 1px solid #263b62;}
[data-testid="stHeader"] {background: transparent;}
.block-container {max-width: 1210px; padding-top: 2rem;}
.wow-hero {padding: 38px 34px; border-radius: 22px; margin: 8px 0 25px;
  background: linear-gradient(110deg, #10254b, #124bb2 72%, #176ad1);
  border: 1px solid #426aa3; box-shadow: 0 14px 42px #04091888;}
.wow-hero h1 {font-size: clamp(1.8rem, 3.6vw, 3.2rem); margin: 6px 0 8px;
  letter-spacing: -.04em; color: #f9fbff;}
.wow-hero p {font-size: 1.08rem; color: #dfeaff; max-width: 660px;}
.wow-kicker {font-size: .8rem; color: #b9f2bc; font-weight: 800;
  letter-spacing: .13em;}
.wow-small {color: #b3c3e3; font-size: .93rem;}
div[data-testid="stMetric"] {background: #112347; border: 1px solid #30456a;
  padding: 14px; border-radius: 14px;}
div[data-testid="stForm"] {background: #0c1933bb; border-radius: 15px;
  border: 1px solid #30456a; padding: 20px;}
.stButton > button[kind="primary"] {background: #2b76d8; border-color: #4c9cfc;}
</style>
""",
    unsafe_allow_html=True,
)

ROOT = Path(os.environ.get("WOW_DATA_DIR", ".wow_workspace")).resolve()
service = GenerationService(ROOT)
favorites = service.jobs.favorites()
jobs = service.jobs.list_recent(200)

st.markdown(
    '<section class="wow-hero"><div class="wow-kicker">WHISPERS OF THE WIRES · COMPOSITION STUDIO</div>'
    '<h1>Music for the moment you are in.</h1>'
    '<p>Describe a situation, shape its emotional journey, and create an original, '
    'editable instrumental arrangement.</p></section>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("🎼 Music Studio")
    page = st.radio(
        "Navigate", ["Compose", "My music", "Feedback & evaluation", "About this project"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("This demo works offline with the rule-based MIDI composer.")
    st.caption("MIDI-GPT is an optional Kaggle GPU workflow, not a confirmed live service.")
    st.caption(f"Workspace: {ROOT.name}")

completed = [job for job in jobs if job["state"] == "completed"]
metrics = st.columns(3)
metrics[0].metric("Compositions created", len(jobs))
metrics[1].metric("Playable compositions", len(completed))
metrics[2].metric("Favorites", len(favorites))


def blueprint_for(job_id: str) -> MusicBlueprint:
    path = service.root / "artifacts" / job_id / "blueprint.json"
    return MusicBlueprint.model_validate_json(path.read_text(encoding="utf-8"))


def show_composition(job_id: str) -> None:
    job = service.jobs.get(job_id)
    if job is None:
        st.warning("Composition not found in the local library.")
        return
    st.subheader("Your composition")
    st.caption(f"Job {job_id[:8]} · {job['provider']} · {job['state']}")
    if job["state"] == "awaiting_cloud":
        st.info(
            "MIDI-GPT is queued for manual Kaggle execution. This is not an audio result. "
            "Follow docs/CLOUD_WORKFLOW.md to prepare, run, and import a verified cloud artifact."
        )
        if st.button("Cancel pending cloud job", key="cancel_" + job_id):
            service.jobs.save(
                job_id, state="cancelled", provider=job["provider"],
                request_id=job["request_id"], data={"reason": "Cancelled by user"},
            )
            st.rerun()
        return
    if job["state"] != "completed":
        st.warning(f"No playable audio for a job in state: {job['state']}")
        return

    bp = blueprint_for(job_id)
    history = versions(service.root, job_id)
    version = st.selectbox("Composition version", history, index=len(history) - 1)
    folder = version_directory(service.root, job_id, version)
    wav_path, midi_path = folder / "composition.wav", folder / "composition.mid"
    if not wav_path.is_file() or not midi_path.is_file():
        st.error("Composition files are missing; cannot play this version.")
        return
    wav = wav_path.read_bytes()
    st.audio(wav, format="audio/wav")
    try:
        audio, rate = sf.read(wav_path, always_2d=True)
        mono = np.mean(audio, axis=1)
        stride = max(1, len(mono) // 900)
        st.line_chart(pd.DataFrame({
            "Time (s)": np.arange(0, len(mono), stride) / rate,
            "Amplitude": mono[::stride],
        }).set_index("Time (s)"), height=180)
    except (OSError, ValueError) as exc:
        st.warning(f"Waveform preview unavailable: {exc}")
    buttons = st.columns(4)
    buttons[0].download_button("Download WAV", wav,
                               file_name=f"whispers-{job_id[:8]}-v{version}.wav",
                               mime="audio/wav", use_container_width=True)
    buttons[1].download_button("Download MIDI", midi_path.read_bytes(),
                               file_name=f"whispers-{job_id[:8]}-v{version}.mid",
                               mime="audio/midi", use_container_width=True)
    archive = build_project_archive(service.root, job_id, version)
    buttons[2].download_button("Project ZIP", archive.read_bytes(),
                               file_name=f"whispers-{job_id[:8]}-v{version}.zip",
                               mime="application/zip", use_container_width=True)
    is_favorite = job_id in favorites
    if buttons[3].button("★ Favorited" if is_favorite else "☆ Favorite",
                         use_container_width=True):
        service.jobs.set_favorite(job_id, not is_favorite)
        st.rerun()
    st.caption(
        f"**Key:** {bp.key.replace('_', ' ')} · **Style:** {bp.style} · "
        f"**Tempo:** {bp.tempo_bpm} BPM · **Bars:** {bp.total_bars} · "
        f"**Seed:** {bp.generation.seed}"
    )
    with st.expander("Emotional journey and score"):
        st.dataframe(pd.DataFrame([s.model_dump() for s in bp.sections]),
                     hide_index=True, use_container_width=True)
        if st.button("Calculate measured audio/MIDI metrics"):
            report = evaluate_files(midi_path, wav_path, bp)
            st.json(report)
    left, right = st.columns(2)
    with left:
        st.subheader("Create a variation")
        st.caption("A new seed creates another arrangement; your original stays saved.")
        if st.button("Generate another take", use_container_width=True):
            variation = bp.model_copy(deep=True)
            variation.request_id = str(uuid.uuid4())
            variation.generation.seed = (variation.generation.seed + 1) % (2**32)
            created = service.create(variation)
            st.session_state["current_job_id"] = created["job_id"]
            st.rerun()
    with right:
        st.subheader("Edit selected bars")
        with st.form("edit_" + job_id):
            track = st.selectbox("Track", [t.id for t in bp.tracks])
            first = st.number_input("First bar (0-indexed)", 0, bp.total_bars - 1, 0)
            last = st.number_input("End bar (exclusive)", int(first) + 1,
                                   bp.total_bars, min(bp.total_bars, int(first) + 4))
            action = st.selectbox("Operation", ["more_energy", "less_dense", "transpose_up"])
            edit_submitted = st.form_submit_button("Save edited version")
        if edit_submitted:
            try:
                saved = create_edit_version(
                    service.root, job_id,
                    EditRequest(base_version=history[-1], track_ids=[track],
                                start_bar=int(first), end_bar_exclusive=int(last),
                                operation=action),
                )
                st.success(
                    f"Version {saved['version']} created; notes outside the selected "
                    "region were preserved."
                )
                st.rerun()
            except (ValueError, OSError) as exc:
                st.error(f"Edit failed: {exc}")
    with st.expander("Leave listener feedback"):
        with st.form("rating_" + job_id):
            selected_section = st.selectbox("Emotional section",
                                            [s.id for s in bp.sections])
            mood_match = st.slider("Mood match (1–5)", 1, 5, 3)
            coherence = st.slider("Musical coherence (1–5)", 1, 5, 3)
            comments = st.text_area("Optional notes", max_chars=500)
            submit_rating = st.form_submit_button("Save rating")
        if submit_rating:
            FeedbackStore(service.root).add(ListenerRating(
                composition_id=job_id, version=version,
                section_id=selected_section, mood_match=mood_match,
                musical_coherence=coherence, comments=comments,
            ))
            st.success("Saved your listener rating locally.")


if page == "Compose":
    st.header("Create your soundtrack")
    with st.form("composition_preferences"):
        story = st.text_area(
            "Tell us the mood, context, or situation",
            value="I feel nervous before a challenge, then confident, finally relieved",
            height=104, max_chars=2000,
        )
        moods = st.text_input(
            "Optional stages (comma-separated)",
            placeholder="nervous, confident, relieved",
            help="Up to four stages. Leave blank for automatic heuristic analysis.",
        )
        first_row = st.columns(4)
        tempo = first_row[0].slider("Tempo (BPM)", 60, 160, 96)
        bars = first_row[1].select_slider("Bars", options=[6, 9, 12, 16, 24], value=12)
        key = first_row[2].selectbox("Musical key",
                                     ["C_major", "G_major", "F_major", "A_minor"])
        style = first_row[3].selectbox(
            "Arrangement style", ["cinematic", "ambient", "lofi", "upbeat", "classical"]
        )
        second_row = st.columns(2)
        provider = second_row[0].selectbox(
            "Generator", ["rule_based", "midigpt"],
            help="The rule-based generator works offline. MIDI-GPT requires Kaggle."
        )
        seed = second_row[1].number_input("Variation seed", 0, 2**32 - 1, 42)
        plan_button = st.form_submit_button("1. Analyze mood and create plan",
                                             type="primary", use_container_width=True)
    if plan_button:
        try:
            stages = [x.strip() for x in moods.split(",") if x.strip()]
            if len(stages) > 4:
                raise ValueError("Use no more than four emotional stages")
            request = PlanningRequest(
                prompt=story, moods=stages or None, tempo_bpm=tempo, total_bars=bars,
                key=key, style=style, seed=int(seed),
            )
            draft = build_blueprint(request)
            draft.generation.provider = provider
            draft.generation.checkpoint = (
                "yellow_medium" if provider == "midigpt" else "rule_based_v1"
            )
            st.session_state["draft_blueprint"] = draft.model_dump()
        except (ValidationError, ValueError) as exc:
            st.error(f"Could not create plan: {exc}")
    if "draft_blueprint" in st.session_state:
        draft = st.session_state["draft_blueprint"]
        st.subheader("2. Review and adjust the emotional timeline")
        st.caption("Mood, valence and arousal are editable. Bar boundaries remain fixed.")
        edited = st.data_editor(
            pd.DataFrame(draft["sections"]),
            hide_index=True, num_rows="fixed",
            disabled=["id", "start_bar", "bar_count"],
            column_config={
                "valence": st.column_config.NumberColumn(
                    "Valence", min_value=-1.0, max_value=1.0, step=0.1
                ),
                "arousal": st.column_config.NumberColumn(
                    "Arousal", min_value=-1.0, max_value=1.0, step=0.1
                ),
            },
            use_container_width=True,
            key="edit_sections_" + draft["request_id"],
        )
        st.caption(
            "The selected style changes the **rule-based** arrangement. "
            "The experimental MIDI-GPT adapter does not promise style conditioning."
        )
        if st.button("3. Compose music", type="primary", use_container_width=True):
            try:
                reviewed = copy.deepcopy(draft)
                reviewed["sections"] = edited.to_dict(orient="records")
                validated = MusicBlueprint.model_validate(reviewed)
                with st.spinner("Creating your MIDI and audio preview..."):
                    created = service.create(validated)
                st.session_state["current_job_id"] = created["job_id"]
                st.session_state.pop("draft_blueprint", None)
                st.rerun()
            except (ValidationError, ValueError, OSError) as exc:
                st.error(f"Could not generate music: {exc}")
    if current := st.session_state.get("current_job_id"):
        show_composition(current)

elif page == "My music":
    st.header("Your music library")
    if not jobs:
        st.info("Your library is empty. Visit Compose to generate your first piece.")
    else:
        filtered = st.checkbox("Favorites only")
        shown = [j for j in jobs if not filtered or j["job_id"] in favorites]
        if not shown:
            st.info("No favorites saved yet.")
        else:
            labels = {
                j["job_id"]: (
                    f"{'★ ' if j['job_id'] in favorites else ''}"
                    f"{j['job_id'][:8]} · {j['provider']} · {j['state']}"
                )
                for j in shown
            }
            selection = st.selectbox(
                "Select composition", [j["job_id"] for j in shown],
                format_func=lambda item: labels[item],
            )
            st.session_state["current_job_id"] = selection
            show_composition(selection)

elif page == "Feedback & evaluation":
    st.header("Evaluation dashboard")
    st.caption("Measured signals are not estimates of perceived emotion.")
    insight = recommend_moods(service.root)
    st.metric("Listener ratings received", insight.get("based_on_ratings", 0))
    if insight.get("sufficient_data"):
        st.dataframe(insight["recommendations"], hide_index=True)
    else:
        st.info("Mood preferences need at least three real ratings per mood.")
    st.markdown(
        "For objective note density, dynamics, timing and audio metrics, "
        "open a finished composition and expand **Emotional journey and score**."
    )
    st.caption("Research protocol: docs/RESEARCH_PROTOCOL.md")

else:
    st.header("What this system actually does")
    st.markdown(
        "**Working locally:** text/mood interpretation, reviewable emotional sections, "
        "four-track MIDI composition, WAV preview, waveform, musical keys/styles, "
        "playback, new variations, safe track/bar editing, version history, favorites, "
        "downloadable MIDI/WAV/ZIP, listener ratings and measurable metrics."
    )
    st.markdown(
        "**Not yet verified:** live pretrained MIDI-GPT generation on Kaggle, "
        "commercial-quality neural audio, real-time audio streaming, audience-tested "
        "emotion accuracy, concurrent-user load targets and production deployment."
    )
    st.info(
        "All local generator outputs are explicitly labeled rule_based. "
        "For the model experiment and acceptance gates, see the repository README "
        "and docs/CLOUD_WORKFLOW.md."
    )
    st.caption("Project: Infosys Springboard · Whispers of the Wires")

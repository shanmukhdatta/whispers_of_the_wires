"""
Whispers of the Wires - AI-Based Music Composer
Main Streamlit Application

A premium, startup-grade AI music generation platform built entirely with 
free and open-source tools.
"""
import os
import sys
import time
import base64
import random
from pathlib import Path
from datetime import datetime

import streamlit as st
from streamlit_option_menu import option_menu

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import APP_NAME, APP_VERSION, COLORS, MOOD_PRESETS, GENRE_MAPPINGS
from app.utils.emotion_analyzer import get_analyzer
from app.utils.music_generator import get_generator
from app.utils.visualizer import get_visualizer
from app.utils.session_manager import get_session_manager, GenerationRecord

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title=f"{APP_NAME} | AI Music Composer",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/whispers-of-the-wires',
        'Report a bug': 'https://github.com/whispers-of-the-wires/issues',
        'About': f"**{APP_NAME}** v{APP_VERSION} - AI-powered music composition"
    }
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "css" / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session
session = get_session_manager()

# ============================================================
# CUSTOM HTML COMPONENTS
# ============================================================

def render_hero():
    """Render the hero section with animated background."""
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">🎵 Whispers of the Wires</h1>
        <p class="hero-subtitle">
            Transform your emotions into music. Describe your mood, context, or situation — 
            our AI composes personalized musical pieces that resonate with your soul.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_particles():
    """Render floating particles animation."""
    particles_html = "<div class=\"particles\">"
    for i in range(20):
        left = random.randint(0, 100)
        delay = random.uniform(0, 15)
        duration = random.uniform(10, 20)
        particles_html += f'<div class="particle" style="left:{left}%;animation-delay:{delay}s;animation-duration:{duration}s;"></div>'
    particles_html += "</div>"
    st.markdown(particles_html, unsafe_allow_html=True)

def render_badge(text: str, variant: str = "primary"):
    """Render a styled badge."""
    return f'<span class="badge badge-{variant}">{text}</span>'

def render_custom_card(title: str, content: str, icon: str = "🎵"):
    """Render a custom card component."""
    st.markdown(f"""
    <div class="custom-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <h3 style="color: #F8FAFC; margin-bottom: 0.5rem; font-size: 1.1rem;">{title}</h3>
        <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def render_mood_preset_card(preset_id: str, preset: dict, col):
    """Render a mood preset card."""
    with col:
        mood_color = preset.get("color", "#6366F1")
        st.markdown(f"""
        <div class="mood-card" style="--mood-color: {mood_color};" 
             onclick="window.parent.postMessage({{type: 'select_mood', id: '{preset_id}'}}, '*')">
            <div class="mood-icon">{preset['name'].split()[0]}</div>
            <div class="mood-name">{" ".join(preset['name'].split()[1:])}</div>
            <div class="mood-desc">{preset['description']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Select", key=f"mood_{preset_id}", use_container_width=True):
            return preset_id
    return None

def render_waveform(audio_path: str):
    """Render waveform visualization."""
    visualizer = get_visualizer()
    svg = visualizer.create_waveform(audio_path, width=700, height=150)
    st.markdown(f"""
    <div class="waveform-container">
        {svg}
    </div>
    """, unsafe_allow_html=True)

def render_spectrogram(audio_path: str):
    """Render spectrogram visualization."""
    visualizer = get_visualizer()
    img_src = visualizer.create_spectrogram(audio_path, width=700, height=250)
    st.markdown(f"""
    <div style="border-radius: 12px; overflow: hidden; margin: 1rem 0;">
        <img src="{img_src}" style="width: 100%; border-radius: 12px;">
    </div>
    """, unsafe_allow_html=True)

def render_mood_wheel(valence: float, arousal: float, dominance: float):
    """Render mood wheel visualization."""
    visualizer = get_visualizer()
    img_src = visualizer.create_mood_visualization(valence, arousal, dominance, width=280, height=280)
    st.markdown(f"""
    <div style="text-align: center;">
        <img src="{img_src}" style="max-width: 100%; border-radius: 12px;">
    </div>
    """, unsafe_allow_html=True)

def render_progress_bar(progress: float, label: str = ""):
    """Render a custom progress bar."""
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #94A3B8; font-size: 0.85rem;">{label}</span>
            <span style="color: #6366F1; font-weight: 600;">{int(progress)}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_generating_animation():
    """Render generating animation."""
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <div class="loading-spinner" style="margin: 0 auto 1.5rem;"></div>
        <h3 style="color: #F8FAFC; margin-bottom: 0.5rem;">Composing Your Music...</h3>
        <p style="color: #64748B;">Our AI is analyzing your mood and crafting the perfect melody</p>
    </div>
    """, unsafe_allow_html=True)

def render_audio_player(audio_path: str, key: str = "audio"):
    """Render enhanced audio player."""
    st.markdown("""
    <div class="audio-container">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">🎧</span>
            <div>
                <div style="color: #F8FAFC; font-weight: 600;">Generated Track</div>
                <div style="color: #64748B; font-size: 0.85rem;">AI Composed</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.audio(audio_path, format="audio/wav")

def render_generation_card(gen: dict, idx: int):
    """Render a generation history card."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"""
        <div class="history-item" style="margin-bottom: 0.5rem;">
            <div class="history-genre">{gen.get('genre', 'Unknown').upper()}</div>
            <div class="history-mood">{gen.get('prompt', 'No description')[:50]}...</div>
            <div class="history-time">{gen.get('timestamp', 'Unknown')}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("Play", key=f"play_hist_{idx}"):
            st.session_state.selected_history = gen
            st.rerun()

    with col3:
        fav_icon = "❤️" if session.is_favorite(gen['generation_id']) else "🤍"
        if st.button(fav_icon, key=f"fav_{idx}"):
            session.toggle_favorite(gen['generation_id'])
            st.rerun()

# ============================================================
# PAGE COMPONENTS
# ============================================================

def render_home_page():
    """Render the home/composer page."""
    render_hero()

    # Main layout
    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.markdown("### 🎛️ Compose Your Music")
        st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

        # Text input
        prompt = st.text_area(
            "Describe your mood or situation",
            placeholder="e.g., peaceful rainy morning with coffee, feeling nostalgic...",
            height=100,
            key="mood_input"
        )

        # Or use presets
        st.markdown("<p style='color: #94A3B8; font-size: 0.9rem; margin-top: 1rem;'>Or choose a preset mood:</p>", unsafe_allow_html=True)

        # Mood preset grid
        presets = MOOD_PRESETS
        preset_cols = st.columns(4)
        selected_preset = None

        for idx, (preset_id, preset) in enumerate(presets.items()):
            col_idx = idx % 4
            with preset_cols[col_idx]:
                mood_color = preset.get("color", "#6366F1")
                if st.button(
                    f"{preset['name']}",
                    key=f"preset_{preset_id}",
                    use_container_width=True,
                    help=preset['description']
                ):
                    selected_preset = preset_id
                    st.session_state.selected_preset = preset_id

        # If preset selected, populate params
        if selected_preset or st.session_state.get('selected_preset'):
            preset_id = selected_preset or st.session_state.get('selected_preset')
            preset = presets.get(preset_id, {})
            if preset:
                st.session_state.valence = preset['valence']
                st.session_state.arousal = preset['arousal']
                st.session_state.dominance = preset['dominance']
                if preset.get('genres'):
                    st.session_state.genre = preset['genres'][0]

        # Advanced parameters
        with st.expander("⚙️ Advanced Parameters"):
            # Sliders for VAD
            valence = st.slider(
                "Valence (Positivity)",
                min_value=-1.0, max_value=1.0, value=st.session_state.get('valence', 0.0),
                step=0.1, key="valence_slider",
                help="How positive or negative the mood is"
            )

            arousal = st.slider(
                "Arousal (Energy)",
                min_value=-1.0, max_value=1.0, value=st.session_state.get('arousal', 0.0),
                step=0.1, key="arousal_slider",
                help="How energetic or calm the mood is"
            )

            dominance = st.slider(
                "Dominance (Intensity)",
                min_value=-1.0, max_value=1.0, value=st.session_state.get('dominance', 0.0),
                step=0.1, key="dominance_slider",
                help="How intense or subdued the mood is"
            )

            # Genre selection
            genre = st.selectbox(
                "Genre",
                options=list(GENRE_MAPPINGS.keys()),
                index=list(GENRE_MAPPINGS.keys()).index(st.session_state.get('genre', 'ambient')) if st.session_state.get('genre') in GENRE_MAPPINGS else 0,
                key="genre_select"
            )

            # Duration
            duration = st.slider(
                "Duration (seconds)",
                min_value=5, max_value=60, value=15,
                step=5, key="duration_slider"
            )

            # Tempo
            tempo = st.slider(
                "Tempo (BPM)",
                min_value=40, max_value=200, value=120,
                step=5, key="tempo_slider"
            )

        # Generate button
        st.markdown("<br>", unsafe_allow_html=True)

        gen_col1, gen_col2 = st.columns([3, 1])
        with gen_col1:
            generate_clicked = st.button(
                "✨ Generate Music",
                use_container_width=True,
                type="primary",
                key="generate_btn"
            )

        with gen_col2:
            use_ai = st.toggle("Use AI", value=False, help="Use MusicGen AI model (requires download)")

    with col_right:
        # Results area
        if generate_clicked:
            # Analyze input
            analyzer = get_analyzer()

            if prompt.strip():
                analysis = analyzer.analyze_text(prompt)
                # Override with slider values if adjusted
                analysis['valence'] = st.session_state.get('valence', analysis['valence'])
                analysis['arousal'] = st.session_state.get('arousal', analysis['arousal'])
                analysis['dominance'] = st.session_state.get('dominance', analysis['dominance'])
            else:
                analysis = {
                    'valence': st.session_state.get('valence', 0.0),
                    'arousal': st.session_state.get('arousal', 0.0),
                    'dominance': st.session_state.get('dominance', 0.0),
                    'original_text': prompt or 'Custom mood settings',
                }

            # Add explicit params
            analysis['genre'] = st.session_state.get('genre', genre)
            analysis['duration'] = st.session_state.get('duration', duration)
            analysis['tempo'] = st.session_state.get('tempo', tempo)

            # Map to music params
            music_params = analyzer.map_to_music_params(analysis)
            music_params['duration'] = st.session_state.get('duration', duration)
            music_params['tempo'] = st.session_state.get('tempo', tempo)

            session.set_mood_analysis(analysis)

            # Show generating animation
            with st.container():
                render_generating_animation()

                # Simulate progress
                progress_bar = st.progress(0)
                for i in range(10):
                    time.sleep(0.3)
                    progress_bar.progress((i + 1) * 10)

                # Generate music
                generator = get_generator()
                result = generator.generate(music_params, use_ai=use_ai)

                if result and result.get('status') == 'completed':
                    # Save to session
                    record = GenerationRecord(
                        generation_id=result['generation_id'],
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        prompt=prompt or f"Valence: {analysis['valence']}, Arousal: {analysis['arousal']}",
                        params=music_params,
                        audio_path=result['audio_path'],
                        midi_path=result.get('midi_path'),
                        duration=result['duration'],
                        genre=music_params['genre'],
                        mood=f"V:{analysis['valence']:.1f} A:{analysis['arousal']:.1f} D:{analysis['dominance']:.1f}"
                    )
                    session.add_generation(record)
                    session.set_current_generation(result)

                    st.success("✅ Music generated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Generation failed. Please try again.")

        # Display current generation
        current = session.get_current_generation()
        if current:
            st.markdown("### 🎶 Your Composition")
            st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

            # Audio player
            if os.path.exists(current['audio_path']):
                render_audio_player(current['audio_path'], key="main_player")

                # Waveform
                render_waveform(current['audio_path'])

                # Action buttons
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                with btn_col1:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.regenerate = True
                        st.rerun()

                with btn_col2:
                    if current.get('midi_path') and os.path.exists(current['midi_path']):
                        with open(current['midi_path'], 'rb') as f:
                            st.download_button(
                                "🎹 MIDI",
                                data=f.read(),
                                file_name=f"{current['generation_id']}.mid",
                                mime="audio/midi",
                                use_container_width=True
                            )
                    else:
                        st.button("🎹 MIDI", disabled=True, use_container_width=True)

                with btn_col3:
                    if os.path.exists(current['audio_path']):
                        with open(current['audio_path'], 'rb') as f:
                            st.download_button(
                                "💾 WAV",
                                data=f.read(),
                                file_name=f"{current['generation_id']}.wav",
                                mime="audio/wav",
                                use_container_width=True
                            )

                with btn_col4:
                    fav = session.is_favorite(current['generation_id'])
                    if st.button("❤️ Favorite" if not fav else "💔 Unfavorite", use_container_width=True):
                        session.toggle_favorite(current['generation_id'])
                        st.rerun()

                # Visualizations tabs
                viz_tabs = st.tabs(["📊 Spectrogram", "🎯 Mood Analysis"])

                with viz_tabs[0]:
                    render_spectrogram(current['audio_path'])

                with viz_tabs[1]:
                    analysis = session.get_mood_analysis()
                    if analysis:
                        col_m1, col_m2 = st.columns([1, 1])
                        with col_m1:
                            render_mood_wheel(
                                analysis.get('valence', 0),
                                analysis.get('arousal', 0),
                                analysis.get('dominance', 0)
                            )
                        with col_m2:
                            st.markdown("#### Mood Analysis")
                            st.markdown(f"**Valence:** {analysis.get('valence', 0):.2f}")
                            st.markdown(f"**Arousal:** {analysis.get('arousal', 0):.2f}")
                            st.markdown(f"**Dominance:** {analysis.get('dominance', 0):.2f}")
                            st.markdown(f"**Genre:** {current.get('params', {}).get('genre', 'Unknown').title()}")
                            st.markdown(f"**Tempo:** {current.get('params', {}).get('tempo', 120)} BPM")
                            st.markdown(f"**Key:** {current.get('params', {}).get('key', 'C Major').replace('_', ' ').title()}")
                            st.markdown(f"**Duration:** {current.get('duration', 10)}s")
                            st.markdown(f"**Method:** {'AI (MusicGen)' if current.get('method') == 'musicgen_ai' else 'Procedural'}")
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%); border-radius: 16px; border: 1px dashed #334155;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎼</div>
                <h3 style="color: #F8FAFC; margin-bottom: 0.5rem;">Ready to Compose</h3>
                <p style="color: #64748B; max-width: 400px; margin: 0 auto;">
                    Describe your mood or select a preset, then click "Generate Music" 
                    to create your personalized composition.
                </p>
            </div>
            """, unsafe_allow_html=True)

def render_history_page():
    """Render the generation history page."""
    st.markdown("## 📚 Generation History")
    st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

    history = session.get_history()

    if not history:
        st.info("No generations yet. Create your first composition on the Home page!")
        return

    # Filter tabs
    tab_all, tab_fav = st.tabs(["All Generations", "Favorites"])

    with tab_all:
        for idx, gen in enumerate(history):
            with st.container():
                render_generation_card(gen, idx)

    with tab_fav:
        favorites = session.get_favorites()
        fav_gens = [g for g in history if g['generation_id'] in favorites]

        if not fav_gens:
            st.info("No favorites yet. Click the heart icon on any generation to add it here!")
        else:
            for idx, gen in enumerate(fav_gens):
                with st.container():
                    render_generation_card(gen, idx)

def render_about_page():
    """Render the about page."""
    st.markdown("## About Whispers of the Wires")
    st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🎵 AI-Powered Music Composition

        **Whispers of the Wires** is an intelligent music composition system that generates 
        personalized musical pieces based on your moods, contexts, and situations.

        #### How It Works

        1. **Describe Your Mood** — Use natural language or select from preset moods
        2. **AI Analysis** — Our emotion recognition engine analyzes your input
        3. **Music Generation** — Advanced AI models compose unique music tailored to you
        4. **Visualize & Export** — View waveforms, spectrograms, and download in multiple formats

        #### Technology Stack

        - **Frontend:** Streamlit with custom CSS/JS
        - **AI Models:** MusicGen (Meta), procedural synthesis
        - **Audio Processing:** librosa, soundfile, pretty_midi
        - **Emotion Analysis:** Custom NLP + VAD model
        - **Visualization:** Matplotlib, SVG

        #### Features

        - 🎼 Multi-track music generation
        - 🎯 Mood & context analysis
        - 🎹 MIDI export
        - 📊 Real-time visualizations
        - 💾 Generation history
        - ❤️ Favorites system

        #### Open Source

        Built entirely with free and open-source tools. No API keys required.
        """)

    with col2:
        # Stats
        st.markdown("### 📊 Stats")

        total_gens = len(session.get_history())
        total_favs = len(session.get_favorites())

        st.markdown(f"""
        <div class="metric-card" style="margin-bottom: 1rem;">
            <div class="metric-value">{total_gens}</div>
            <div class="metric-label">Generations</div>
        </div>
        <div class="metric-card" style="margin-bottom: 1rem;">
            <div class="metric-value">{total_favs}</div>
            <div class="metric-label">Favorites</div>
        </div>
        """, unsafe_allow_html=True)

        # Version info
        st.markdown(f"""
        <div class="custom-card">
            <div style="font-size: 0.85rem; color: #94A3B8;">
                <div><strong>Version:</strong> {APP_VERSION}</div>
                <div><strong>Status:</strong> <span style="color: #10B981;">● Active</span></div>
                <div><strong>License:</strong> MIT</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎵</div>
            <h2 style="color: #F8FAFC; font-size: 1.2rem; margin: 0;">{APP_NAME}</h2>
            <p style="color: #64748B; font-size: 0.8rem; margin-top: 0.25rem;">v{APP_VERSION}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

        # Navigation
        selected = option_menu(
            menu_title=None,
            options=["Home", "History", "About"],
            icons=["house", "clock-history", "info-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#64748B", "font-size": "1.2rem"},
                "nav-link": {
                    "color": "#94A3B8",
                    "font-size": "0.95rem",
                    "text-align": "left",
                    "padding": "0.75rem 1rem",
                    "border-radius": "8px",
                    "margin": "0.25rem 0",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #6366F1, #4F46E5)",
                    "color": "white",
                    "font-weight": "600",
                },
            }
        )

        st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

        # Quick stats
        history = session.get_history()
        if history:
            st.markdown(f"""
            <div style="padding: 0.5rem;">
                <div style="color: #64748B; font-size: 0.8rem; margin-bottom: 0.5rem;">Quick Stats</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: #94A3B8; font-size: 0.85rem;">Generations</span>
                    <span style="color: #6366F1; font-weight: 600;">{len(history)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94A3B8; font-size: 0.85rem;">Favorites</span>
                    <span style="color: #EC4899; font-weight: 600;">{len(session.get_favorites())}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class=\"custom-divider\"></div>", unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div style="padding: 0.5rem; text-align: center;">
            <p style="color: #475569; font-size: 0.75rem;">
                Built with 💜 using free & open-source tools
            </p>
        </div>
        """, unsafe_allow_html=True)

        return selected

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application entry point."""
    # Render particles background
    render_particles()

    # Render sidebar and get selected page
    selected_page = render_sidebar()

    # Route to page
    if selected_page == "Home":
        render_home_page()
    elif selected_page == "History":
        render_history_page()
    elif selected_page == "About":
        render_about_page()

if __name__ == "__main__":
    main()

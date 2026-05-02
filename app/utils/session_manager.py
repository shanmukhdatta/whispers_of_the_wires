"""Session state management for the app."""
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class GenerationRecord:
    """Record of a music generation."""
    generation_id: str
    timestamp: str
    prompt: str
    params: Dict[str, Any]
    audio_path: str
    midi_path: Optional[str]
    duration: int
    genre: str
    mood: str
    status: str = "completed"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "GenerationRecord":
        return cls(**data)


class SessionManager:
    """Manages user session state and generation history."""

    def __init__(self):
        self._init_session()

    def _init_session(self):
        """Initialize session state variables."""
        import streamlit as st

        defaults = {
            "generation_history": [],
            "current_generation": None,
            "favorites": [],
            "user_preferences": {
                "default_genre": "ambient",
                "default_duration": 15,
                "auto_play": True,
                "visualization_mode": "waveform",
            },
            "mood_analysis": None,
            "is_generating": False,
            "generation_count": 0,
            "show_tutorial": True,
            "current_page": "home",
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def add_generation(self, record: GenerationRecord):
        """Add a generation to history."""
        import streamlit as st
        st.session_state.generation_history.insert(0, record.to_dict())
        st.session_state.generation_count += 1
        st.session_state.current_generation = record.to_dict()

        # Keep only last 50 generations
        if len(st.session_state.generation_history) > 50:
            st.session_state.generation_history = st.session_state.generation_history[:50]

    def get_history(self) -> List[Dict]:
        """Get generation history."""
        import streamlit as st
        return st.session_state.generation_history

    def get_current_generation(self) -> Optional[Dict]:
        """Get current generation."""
        import streamlit as st
        return st.session_state.current_generation

    def set_current_generation(self, generation: Dict):
        """Set current generation."""
        import streamlit as st
        st.session_state.current_generation = generation

    def toggle_favorite(self, generation_id: str):
        """Toggle favorite status."""
        import streamlit as st
        if generation_id in st.session_state.favorites:
            st.session_state.favorites.remove(generation_id)
        else:
            st.session_state.favorites.append(generation_id)

    def is_favorite(self, generation_id: str) -> bool:
        """Check if generation is favorited."""
        import streamlit as st
        return generation_id in st.session_state.favorites

    def get_favorites(self) -> List[str]:
        """Get favorited generation IDs."""
        import streamlit as st
        return st.session_state.favorites

    def set_generating(self, status: bool):
        """Set generation status."""
        import streamlit as st
        st.session_state.is_generating = status

    def is_generating(self) -> bool:
        """Check if generation is in progress."""
        import streamlit as st
        return st.session_state.is_generating

    def set_mood_analysis(self, analysis: Dict):
        """Set current mood analysis."""
        import streamlit as st
        st.session_state.mood_analysis = analysis

    def get_mood_analysis(self) -> Optional[Dict]:
        """Get current mood analysis."""
        import streamlit as st
        return st.session_state.mood_analysis

    def update_preference(self, key: str, value: Any):
        """Update a user preference."""
        import streamlit as st
        st.session_state.user_preferences[key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        import streamlit as st
        return st.session_state.user_preferences.get(key, default)

    def set_page(self, page: str):
        """Set current page."""
        import streamlit as st
        st.session_state.current_page = page

    def get_page(self) -> str:
        """Get current page."""
        import streamlit as st
        return st.session_state.current_page

    def dismiss_tutorial(self):
        """Dismiss tutorial."""
        import streamlit as st
        st.session_state.show_tutorial = False

    def should_show_tutorial(self) -> bool:
        """Check if tutorial should be shown."""
        import streamlit as st
        return st.session_state.show_tutorial


# Singleton
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

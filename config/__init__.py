"""Configuration management for Whispers of the Wires."""
import os
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / "app"
ASSETS_DIR = APP_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR = BASE_DIR / "uploads"
MODEL_DIR = BASE_DIR / "models"

# Create directories
for dir_path in [OUTPUT_DIR, UPLOAD_DIR, MODEL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# App Settings
APP_NAME = os.getenv("APP_NAME", "Whispers of the Wires")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "whispers-dev-key-change-in-production")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8501"))
API_PORT = int(os.getenv("API_PORT", "8000"))

# Model Settings
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "facebook/musicgen-small")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "facebook/musicgen-small")
MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", str(MODEL_DIR)))

# Generation
DEFAULT_DURATION = int(os.getenv("DEFAULT_DURATION", "10"))
MAX_DURATION = int(os.getenv("MAX_DURATION", "120"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "1.0"))

# Audio
SAMPLE_RATE = 32000
MAX_FILE_SIZE_MB = 50

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Colors (Premium Startup Palette)
COLORS = {
    "primary": "#6366F1",        # Indigo 500
    "primary_dark": "#4F46E5",   # Indigo 600
    "primary_light": "#818CF8",  # Indigo 400
    "secondary": "#EC4899",      # Pink 500
    "accent": "#06B6D4",         # Cyan 500
    "success": "#10B981",        # Emerald 500
    "warning": "#F59E0B",        # Amber 500
    "danger": "#EF4444",         # Red 500
    "dark": "#0F172A",           # Slate 900
    "darker": "#020617",         # Slate 950
    "light": "#F8FAFC",          # Slate 50
    "muted": "#64748B",          # Slate 500
    "card_bg": "#1E293B",        # Slate 800
    "card_border": "#334155",    # Slate 700
    "gradient_start": "#6366F1",
    "gradient_end": "#EC4899",
}

# Mood Presets
MOOD_PRESETS = {
    "peaceful_morning": {
        "name": "☀️ Peaceful Morning",
        "valence": 0.6,
        "arousal": -0.3,
        "dominance": 0.1,
        "description": "Soft, warm, and gentle like sunrise",
        "genres": ["ambient", "acoustic", "classical"],
        "color": "#F59E0B",
    },
    "late_night_work": {
        "name": "🌙 Late Night Work",
        "valence": 0.2,
        "arousal": -0.4,
        "dominance": 0.5,
        "description": "Focused, ambient, electronic",
        "genres": ["electronic", "ambient", "lofi"],
        "color": "#6366F1",
    },
    "workout_energy": {
        "name": "💪 Workout Energy",
        "valence": 0.7,
        "arousal": 0.9,
        "dominance": 0.8,
        "description": "High energy, driving, powerful",
        "genres": ["edm", "rock", "hip-hop"],
        "color": "#EF4444",
    },
    "rainy_day": {
        "name": "🌧️ Rainy Day",
        "valence": 0.1,
        "arousal": -0.6,
        "dominance": -0.3,
        "description": "Melancholic, piano, slow",
        "genres": ["piano", "ambient", "jazz"],
        "color": "#06B6D4",
    },
    "celebration": {
        "name": "🎉 Celebration",
        "valence": 0.9,
        "arousal": 0.8,
        "dominance": 0.7,
        "description": "Triumphant, orchestral, joyful",
        "genres": ["orchestral", "pop", "funk"],
        "color": "#F59E0B",
    },
    "deep_focus": {
        "name": "🧘 Deep Focus",
        "valence": 0.4,
        "arousal": -0.8,
        "dominance": -0.5,
        "description": "Minimal, drone, meditative",
        "genres": ["drone", "ambient", "minimal"],
        "color": "#10B981",
    },
    "creative_flow": {
        "name": "🎨 Creative Flow",
        "valence": 0.8,
        "arousal": 0.5,
        "dominance": 0.4,
        "description": "Inspiring, uplifting, imaginative",
        "genres": ["indie", "folk", "synthwave"],
        "color": "#EC4899",
    },
    "romantic_evening": {
        "name": "💕 Romantic Evening",
        "valence": 0.7,
        "arousal": 0.2,
        "dominance": 0.3,
        "description": "Warm, intimate, soulful",
        "genres": ["jazz", "rnb", "soul"],
        "color": "#EC4899",
    },
}

# Genre Mappings
GENRE_MAPPINGS = {
    "ambient": {"tempo_range": (60, 90), "key_bias": "minor", "instruments": ["pad", "strings"]},
    "acoustic": {"tempo_range": (70, 110), "key_bias": "major", "instruments": ["guitar", "piano"]},
    "classical": {"tempo_range": (60, 120), "key_bias": "both", "instruments": ["piano", "strings", "orchestra"]},
    "electronic": {"tempo_range": (100, 140), "key_bias": "minor", "instruments": ["synth", "bass", "drums"]},
    "lofi": {"tempo_range": (70, 90), "key_bias": "minor", "instruments": ["piano", "bass", "drums"]},
    "edm": {"tempo_range": (120, 150), "key_bias": "minor", "instruments": ["synth", "bass", "drums"]},
    "rock": {"tempo_range": (100, 140), "key_bias": "both", "instruments": ["guitar", "bass", "drums"]},
    "hip-hop": {"tempo_range": (80, 110), "key_bias": "minor", "instruments": ["bass", "drums", "synth"]},
    "piano": {"tempo_range": (60, 100), "key_bias": "both", "instruments": ["piano"]},
    "jazz": {"tempo_range": (80, 140), "key_bias": "both", "instruments": ["piano", "bass", "sax"]},
    "orchestral": {"tempo_range": (60, 130), "key_bias": "both", "instruments": ["strings", "brass", "woodwinds"]},
    "pop": {"tempo_range": (90, 130), "key_bias": "major", "instruments": ["synth", "guitar", "drums"]},
    "funk": {"tempo_range": (100, 130), "key_bias": "major", "instruments": ["bass", "guitar", "drums"]},
    "drone": {"tempo_range": (40, 60), "key_bias": "minor", "instruments": ["pad", "synth"]},
    "minimal": {"tempo_range": (50, 80), "key_bias": "both", "instruments": ["piano", "strings"]},
    "indie": {"tempo_range": (80, 120), "key_bias": "both", "instruments": ["guitar", "synth", "drums"]},
    "folk": {"tempo_range": (70, 110), "key_bias": "major", "instruments": ["guitar", "strings"]},
    "synthwave": {"tempo_range": (90, 130), "key_bias": "minor", "instruments": ["synth", "bass", "drums"]},
    "rnb": {"tempo_range": (70, 100), "key_bias": "major", "instruments": ["piano", "bass", "drums"]},
    "soul": {"tempo_range": (70, 110), "key_bias": "major", "instruments": ["piano", "bass", "horns"]},
}

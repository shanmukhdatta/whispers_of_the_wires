"""Basic tests for Whispers of the Wires."""
import pytest
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.emotion_analyzer import EmotionAnalyzer
from app.utils.music_generator import MusicGenerator


class TestEmotionAnalyzer:
    """Test emotion analysis."""

    def test_initialization(self):
        analyzer = EmotionAnalyzer()
        assert analyzer is not None

    def test_text_analysis(self):
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_text("happy and energetic")
        assert "valence" in result
        assert "arousal" in result
        assert result["valence"] > 0
        assert result["arousal"] > 0

    def test_preset_retrieval(self):
        analyzer = EmotionAnalyzer()
        preset = analyzer.get_preset("peaceful_morning")
        assert preset is not None
        assert "valence" in preset


class TestMusicGenerator:
    """Test music generation."""

    def test_initialization(self):
        gen = MusicGenerator()
        assert gen is not None

    def test_procedural_generation(self):
        gen = MusicGenerator()
        params = {
            "duration": 5,
            "tempo": 120,
            "key": "C_major",
            "genre": "ambient",
            "valence": 0.5,
            "arousal": -0.3,
            "dominance": 0.1,
        }
        result = gen.generate(params, use_ai=False)
        assert result["status"] == "completed"
        assert "audio_path" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

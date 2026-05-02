"""Emotion and context analysis for music generation."""
import re
import random
from typing import Dict, List, Tuple, Optional
from config import MOOD_PRESETS, GENRE_MAPPINGS


class EmotionAnalyzer:
    """Analyzes user input to extract emotional and musical parameters."""

    # Emotion keyword mappings
    VALENCE_KEYWORDS = {
        "positive": ["happy", "joy", "love", "excited", "cheerful", "bright", "uplifting", 
                     "optimistic", "peaceful", "calm", "content", "satisfied", "grateful",
                     "blissful", "elated", "euphoric", "ecstatic", "delighted", "pleased",
                     "warm", "cozy", "comfortable", "serene", "tranquil", "harmonious",
                     "celebration", "party", "fun", "playful", "lighthearted", "romantic",
                     "inspiring", "motivated", "hopeful", "confident", "proud", "triumphant"],
        "negative": ["sad", "depressed", "melancholic", "gloomy", "dark", "somber", "mournful",
                     "angry", "frustrated", "irritated", "furious", "aggressive", "intense",
                     "anxious", "nervous", "worried", "stressed", "tense", "uneasy",
                     "lonely", "isolated", "empty", "hollow", "numb", "distant",
                     "disappointed", "regretful", "guilty", "ashamed", "embarrassed",
                     "fearful", "scared", "terrified", "panicked", "horrified"]
    }

    AROUSAL_KEYWORDS = {
        "high": ["energetic", "intense", "powerful", "aggressive", "fast", "driving",
                 "pumping", "explosive", "dynamic", "vigorous", "forceful", "strong",
                 "workout", "exercise", "running", "dancing", "party", "club",
                 "excited", "thrilled", "amped", "fired up", "hyped", "wild",
                 "chaotic", "frantic", "frenzied", "hectic", "turbulent"],
        "low": ["calm", "peaceful", "relaxing", "gentle", "soft", "slow", "quiet",
                "soothing", "tranquil", "serene", "mellow", "laid back", "chill",
                "sleepy", "tired", "drowsy", "lazy", "lethargic", "sluggish",
                "meditation", "yoga", "spa", "sleep", "rest", "recovery",
                "ambient", "drone", "minimal", "subtle", "delicate", "fragile"]
    }

    DOMINANCE_KEYWORDS = {
        "high": ["powerful", "strong", "confident", "dominant", "commanding", "authoritative",
                 "epic", "grand", "majestic", "imposing", "massive", "huge",
                 "intense", "heavy", "thick", "dense", "complex", "sophisticated",
                 "orchestral", "cinematic", "soundtrack", "trailer", "battle", "victory"],
        "low": ["weak", "vulnerable", "fragile", "delicate", "gentle", "tender",
                "intimate", "personal", "private", "quiet", "soft", "subtle",
                "simple", "minimal", "sparse", "light", "airy", "ethereal",
                "ambient", "background", "atmospheric", "dreamy", "floating"]
    }

    GENRE_KEYWORDS = {
        "ambient": ["ambient", "atmospheric", "space", "cosmic", "ethereal", "dreamy"],
        "acoustic": ["acoustic", "unplugged", "folk", "guitar", "piano solo"],
        "classical": ["classical", "orchestra", "symphony", "baroque", "romantic era"],
        "electronic": ["electronic", "synth", "techno", "house", "trance"],
        "lofi": ["lofi", "lo-fi", "chillhop", "study", "relax"],
        "edm": ["edm", "dance", "festival", "drop", "bass"],
        "rock": ["rock", "guitar", "band", "alternative", "indie rock"],
        "hip-hop": ["hip-hop", "rap", "beats", "trap", "boom bap"],
        "piano": ["piano", "solo piano", "pianist", "keyboard"],
        "jazz": ["jazz", "swing", "bebop", "smooth jazz", "improvisation"],
        "orchestral": ["orchestral", "cinematic", "film score", "epic", "trailer"],
        "pop": ["pop", "catchy", "radio", "chart", "mainstream"],
        "funk": ["funk", "groove", "disco", "soulful", "rhythmic"],
        "drone": ["drone", "meditation", "om", "chant", "long tones"],
        "minimal": ["minimal", "simple", "clean", "sparse", "reduced"],
        "indie": ["indie", "alternative", "underground", "artistic", "creative"],
        "folk": ["folk", "traditional", "storytelling", "campfire", "acoustic"],
        "synthwave": ["synthwave", "retrowave", "80s", "vaporwave", "nostalgic"],
        "rnb": ["rnb", "r&b", "soul", "smooth", "groove"],
        "soul": ["soul", "motown", "gospel", "emotional", "heartfelt"],
    }

    def __init__(self):
        self.presets = MOOD_PRESETS
        self.genre_mappings = GENRE_MAPPINGS

    def analyze_text(self, text: str) -> Dict:
        """Analyze free-form text to extract emotion parameters."""
        text_lower = text.lower()

        # Calculate valence
        valence = self._calculate_dimension(text_lower, self.VALENCE_KEYWORDS)

        # Calculate arousal
        arousal = self._calculate_dimension(text_lower, self.AROUSAL_KEYWORDS)

        # Calculate dominance
        dominance = self._calculate_dimension(text_lower, self.DOMINANCE_KEYWORDS)

        # Detect genre
        genre = self._detect_genre(text_lower)

        # Detect tempo hints
        tempo = self._detect_tempo(text_lower)

        # Detect duration hints
        duration = self._detect_duration(text_lower)

        return {
            "valence": round(valence, 2),
            "arousal": round(arousal, 2),
            "dominance": round(dominance, 2),
            "genre": genre,
            "tempo": tempo,
            "duration": duration,
            "original_text": text,
        }

    def _calculate_dimension(self, text: str, keywords: Dict[str, List[str]]) -> float:
        """Calculate emotion dimension score from -1 to 1."""
        positive_score = sum(1 for word in keywords["positive"] if word in text)
        negative_score = sum(1 for word in keywords["negative"] if word in text)

        total = positive_score + negative_score
        if total == 0:
            return 0.0

        return (positive_score - negative_score) / total

    def _detect_genre(self, text: str) -> Optional[str]:
        """Detect genre from text."""
        scores = {}
        for genre, keywords in self.GENRE_KEYWORDS.items():
            score = sum(1 for word in keywords if word in text)
            if score > 0:
                scores[genre] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def _detect_tempo(self, text: str) -> Optional[int]:
        """Detect tempo hints from text."""
        # Look for explicit BPM mentions
        bpm_match = re.search(r'(\d+)\s*(?:bpm|beats? per minute)', text)
        if bpm_match:
            return int(bpm_match.group(1))

        # Look for speed descriptors
        if any(word in text for word in ["fast", "quick", "rapid", "speedy", "upbeat"]):
            return random.randint(120, 160)
        elif any(word in text for word in ["slow", "gentle", "calm", "relaxing", "peaceful"]):
            return random.randint(60, 90)
        elif any(word in text for word in ["medium", "moderate", "mid-tempo"]):
            return random.randint(90, 120)

        return None

    def _detect_duration(self, text: str) -> Optional[int]:
        """Detect duration hints from text."""
        # Look for explicit duration mentions
        sec_match = re.search(r'(\d+)\s*(?:seconds?|secs?)', text)
        if sec_match:
            return min(int(sec_match.group(1)), 120)

        min_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text)
        if min_match:
            return min(int(min_match.group(1)) * 60, 120)

        return None

    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """Get a mood preset by ID."""
        return self.presets.get(preset_id)

    def get_all_presets(self) -> Dict:
        """Get all available mood presets."""
        return self.presets

    def map_to_music_params(self, analysis: Dict) -> Dict:
        """Map emotion analysis to concrete music generation parameters."""
        valence = analysis.get("valence", 0)
        arousal = analysis.get("arousal", 0)
        dominance = analysis.get("dominance", 0)
        genre = analysis.get("genre")

        # Determine key
        if valence > 0.3:
            key = random.choice(["C_major", "G_major", "D_major", "F_major", "A_major"])
        elif valence < -0.3:
            key = random.choice(["A_minor", "E_minor", "D_minor", "B_minor", "G_minor"])
        else:
            key = random.choice(["C_major", "A_minor", "G_major", "E_minor", "F_major"])

        # Determine tempo
        if analysis.get("tempo"):
            tempo = analysis["tempo"]
        else:
            base_tempo = 60 + int((arousal + 1) * 60)  # 60-180 BPM
            tempo = max(40, min(200, base_tempo + random.randint(-10, 10)))

        # Determine genre if not specified
        if not genre:
            if arousal > 0.5 and valence > 0.3:
                genre = random.choice(["edm", "pop", "funk"])
            elif arousal > 0.5 and valence < -0.3:
                genre = random.choice(["rock", "electronic"])
            elif arousal < -0.3 and valence > 0.3:
                genre = random.choice(["ambient", "acoustic", "classical"])
            elif arousal < -0.3 and valence < -0.3:
                genre = random.choice(["piano", "ambient", "drone"])
            else:
                genre = random.choice(["ambient", "lofi", "classical"])

        # Get genre mapping
        genre_info = self.genre_mappings.get(genre, self.genre_mappings["ambient"])

        # Determine duration
        duration = analysis.get("duration") or random.randint(10, 30)
        duration = min(duration, 120)

        # Determine instrumentation
        instruments = genre_info["instruments"]

        # Determine complexity based on dominance
        complexity = "high" if dominance > 0.3 else "medium" if dominance > -0.3 else "low"

        return {
            "key": key,
            "tempo": tempo,
            "genre": genre,
            "duration": duration,
            "instruments": instruments,
            "complexity": complexity,
            "valence": valence,
            "arousal": arousal,
            "dominance": dominance,
        }


# Singleton instance
_analyzer = None

def get_analyzer() -> EmotionAnalyzer:
    """Get or create the emotion analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = EmotionAnalyzer()
    return _analyzer

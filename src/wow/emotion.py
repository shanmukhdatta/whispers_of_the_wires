"""Transparent English text analysis with an optional, lazy-loaded pretrained classifier."""
from __future__ import annotations

import re
from dataclasses import dataclass


EMOTIONS: dict[str, tuple[float, float, tuple[str, ...]]] = {
    "nervous": (-0.6, 0.7, ("nervous", "anxious", "fear", "worried", "tense")),
    "confident": (0.6, 0.75, ("confident", "brave", "courage", "hopeful", "determined")),
    "relieved": (0.7, -0.4, ("relieved", "relief", "safe", "resolved", "content")),
    "sad": (-0.75, -0.5, ("sad", "melancholic", "lonely", "grief", "heartbroken")),
    "joyful": (0.9, 0.8, ("joyful", "celebrating", "happy", "excited", "celebration")),
    "peaceful": (0.65, -0.75, ("peaceful", "calm", "quiet", "serene", "relaxed")),
    "mysterious": (-0.2, 0.25, ("mysterious", "curious", "uncertain", "mystery")),
}
DEFAULT = ("nervous", "confident", "relieved")
SPLITTER = re.compile(r"\b(?:and then|then|finally|eventually|afterwards|later)\b|[;\n]", re.I)


@dataclass(frozen=True)
class EmotionSignal:
    mood: str
    valence: float
    arousal: float
    evidence: tuple[str, ...]
    needs_review: bool


def normalize_mood(value: str) -> EmotionSignal:
    text = value.strip().lower()
    for mood, (valence, arousal, keywords) in EMOTIONS.items():
        hits = tuple(word for word in keywords if word in text)
        if hits:
            return EmotionSignal(mood, valence, arousal, hits, False)
    return EmotionSignal("mysterious", -0.2, 0.25, (), True)


def analyze_prompt(prompt: str) -> list[EmotionSignal]:
    parts = [part.strip() for part in SPLITTER.split(prompt) if part.strip()]
    if not parts:
        raise ValueError("Prompt must not be empty")
    signals = [normalize_mood(part) for part in parts[:4]]
    if len(signals) == 1:
        # Explicit fallback: proposing three stages is an artistic suggestion, NOT inference.
        return [normalize_mood(m) for m in DEFAULT]
    return signals


def optional_transformer_scores(text: str) -> list[dict[str, float | str]]:
    """Opt-in CPU inference. Never download a model in a default request or CI."""
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Install the optional 'emotion' dependencies") from exc
    classifier = pipeline(
        task="text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        device=-1,
        top_k=None,
    )
    scores = classifier(text)
    if scores and isinstance(scores[0], list):
        scores = scores[0]
    return [{"label": str(item["label"]), "score": float(item["score"])}
            for item in scores]

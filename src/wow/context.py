"""Keyword-based context parsing; never claim weather or device observations."""
from __future__ import annotations

import re

from wow.contracts import ContextInfo

VOCABULARY = {
    "weather": {
        "rainy": ("rain", "rainy", "raining", "rainstorm"),
        "sunny": ("sun", "sunny", "sunshine"),
        "snowy": ("snow", "snowy", "snowfall"),
        "windy": ("wind", "windy", "breeze"),
    },
    "time_of_day": {
        "morning": ("morning", "sunrise", "dawn"),
        "afternoon": ("afternoon", "noon"),
        "evening": ("evening", "sunset", "dusk"),
        "night": ("night", "midnight", "bedtime"),
    },
    "activity": {
        "study": ("study", "studying", "exam", "homework", "reading"),
        "relax": ("relax", "relaxing", "meditating", "resting"),
        "exercise": ("running", "exercise", "workout", "jogging"),
        "travel": ("travel", "journey", "train", "commute"),
        "work": ("working", "office", "coding"),
    },
}


def extract_context(
    prompt: str, *, activity: str | None = None,
    weather: str | None = None, time_of_day: str | None = None,
) -> ContextInfo:
    """Find explicit words, and let user-provided fields override extracted words."""
    inferred = {}
    for field, options in VOCABULARY.items():
        inferred[field] = None
        for canonical, terms in options.items():
            if any(re.search(r"\b" + re.escape(term) + r"\b", prompt, re.I)
                   for term in terms):
                inferred[field] = canonical
                break
    overrides = {"activity": activity, "weather": weather, "time_of_day": time_of_day}
    return ContextInfo(
        activity=activity or inferred["activity"],
        weather=weather or inferred["weather"],
        time_of_day=time_of_day or inferred["time_of_day"],
        source=("explicit" if any(v is not None for v in overrides.values())
                else "prompt" if any(inferred.values()) else "unspecified"),
    )

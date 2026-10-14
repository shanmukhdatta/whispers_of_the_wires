"""Phase 2 HTTP contracts for emotion analysis and validated blueprint creation."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from wow.contracts import MusicBlueprint
from wow.emotion import analyze_prompt
from wow.planning import PlanningRequest, build_blueprint

app = FastAPI(title="Whispers of the Wires API", version="0.2.0")


class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0"}


@app.post("/api/v1/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    signals = analyze_prompt(request.prompt)
    return {
        "segments": [
            {"mood": signal.mood, "valence": signal.valence,
             "arousal": signal.arousal, "evidence": signal.evidence,
             "needs_review": signal.needs_review}
            for signal in signals
        ],
        "analysis_mode": "heuristic",
        "note": "Mood stages are suggestions; edit before generation.",
    }


@app.post("/api/v1/blueprints", response_model=MusicBlueprint)
def create_blueprint(request: PlanningRequest) -> MusicBlueprint:
    return build_blueprint(request)

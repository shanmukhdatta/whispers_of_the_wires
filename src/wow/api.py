"""Phase 3: planning, local generation and explicit Kaggle artifact import."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from wow.contracts import MusicBlueprint
from wow.emotion import analyze_prompt
from wow.generation import GenerationService
from wow.planning import PlanningRequest, build_blueprint

app = FastAPI(title="Whispers of the Wires API", version="0.3.0")


def service() -> GenerationService:
    return GenerationService(Path(os.environ.get("WOW_DATA_DIR", ".wow_workspace")))


class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class ImportRequest(BaseModel):
    folder_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.3.0"}


@app.post("/api/v1/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    signals = analyze_prompt(request.prompt)
    return {
        "segments": [
            {"mood": s.mood, "valence": s.valence, "arousal": s.arousal,
             "evidence": s.evidence, "needs_review": s.needs_review}
            for s in signals
        ],
        "analysis_mode": "heuristic",
        "note": "Mood stages are suggestions; edit before generation.",
    }


@app.post("/api/v1/blueprints", response_model=MusicBlueprint)
def create_blueprint(request: PlanningRequest) -> MusicBlueprint:
    return build_blueprint(request)


@app.post("/api/v1/jobs", status_code=202)
def create_job(blueprint: MusicBlueprint) -> dict:
    return service().create(blueprint)


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = service().jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job


@app.post("/api/v1/jobs/{job_id}/import")
def import_cloud_job(job_id: str, request: ImportRequest) -> dict:
    try:
        return service().import_kaggle(job_id, request.folder_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

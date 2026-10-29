"""Phase 4: local planning, generation, editable composition versions, downloads."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from wow.audio_export import CodecUnavailable, convert_wav_to_mp3
from wow.context import extract_context
from wow.contracts import MusicBlueprint
from wow.editing import EditRequest, create_edit_version, version_directory, versions
from wow.emotion import analyze_prompt
from wow.evaluation import FeedbackStore, ListenerRating, evaluate_files
from wow.generation import GenerationService
from wow.library import LibraryStore
from wow.planning import PlanningRequest, build_blueprint
from wow.preferences import recommend_moods
from wow.project_archive import build_project_archive
from wow.variations import VariationRequest, vary

app = FastAPI(title="Whispers of the Wires API", version="0.4.0")


def service() -> GenerationService:
    return GenerationService(Path(os.environ.get("WOW_DATA_DIR", ".wow_workspace")))


class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class ImportRequest(BaseModel):
    folder_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.0"}


@app.post("/api/v1/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    signals = analyze_prompt(request.prompt)
    return {"segments": [
        {"mood": s.mood, "valence": s.valence, "arousal": s.arousal,
         "evidence": s.evidence, "needs_review": s.needs_review}
        for s in signals
    ], "analysis_mode": "heuristic",
        "note": "Mood stages are suggestions; edit before generation."}


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


@app.get("/api/v1/compositions/{composition_id}")
def composition(composition_id: str) -> dict:
    job = service().jobs.get(composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        history = versions(service().root, composition_id)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"job": job, "versions": history, "latest": history[-1] if history else None}


@app.get("/api/v1/compositions/{composition_id}/versions")
def history(composition_id: str) -> dict:
    return composition(composition_id)


@app.post("/api/v1/compositions/{composition_id}/edits")
def edit(composition_id: str, request: EditRequest) -> dict:
    job = service().jobs.get(composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        return create_edit_version(service().root, composition_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/compositions/{composition_id}/assets/{asset}")
def download(composition_id: str, asset: str, version: int = 1) -> FileResponse:
    if asset not in ("composition.mid", "composition.wav", "composition.mp3"):
        raise HTTPException(status_code=404, detail="Unsupported asset")
    job = service().jobs.get(composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        folder = version_directory(service().root, composition_id, version)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if version not in versions(service().root, composition_id):
        raise HTTPException(status_code=404, detail="Unknown version")
    path = folder / asset
    if asset == "composition.mp3" and not path.is_file():
        try:
            convert_wav_to_mp3(folder / "composition.wav", path)
        except CodecUnavailable as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except (OSError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(str(path), filename=asset)


class EvaluateRequest(BaseModel):
    composition_id: str
    version: int = Field(default=1, ge=1)


@app.post("/api/v1/evaluations")
def evaluate(request: EvaluateRequest) -> dict:
    job = service().jobs.get(request.composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        folder = version_directory(service().root, request.composition_id, request.version)
        blueprint = MusicBlueprint.model_validate_json(
            (version_directory(service().root, request.composition_id, 1)
             / "blueprint.json").read_text(encoding="utf-8"))
        return evaluate_files(folder / "composition.mid", folder / "composition.wav", blueprint)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/feedback", status_code=201)
def submit_feedback(rating: ListenerRating) -> dict:
    job = service().jobs.get(rating.composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    if rating.version not in versions(service().root, rating.composition_id):
        raise HTTPException(status_code=404, detail="Version not found")
    blueprint_path = version_directory(
        service().root, rating.composition_id, 1
    ) / "blueprint.json"
    blueprint = MusicBlueprint.model_validate_json(
        blueprint_path.read_text(encoding="utf-8")
    )
    if rating.section_id not in {s.id for s in blueprint.sections}:
        raise HTTPException(status_code=422, detail="Unknown emotional section")
    return FeedbackStore(service().root).add(rating)


@app.get("/api/v1/feedback/summary/{composition_id}")
def feedback_summary(composition_id: str) -> dict:
    if service().jobs.get(composition_id) is None:
        raise HTTPException(status_code=404, detail="Composition not found")
    return FeedbackStore(service().root).summarize(composition_id)


@app.get("/api/v1/compositions/{composition_id}/export")
def export_project(composition_id: str, version: int = 1) -> FileResponse:
    job = service().jobs.get(composition_id)
    if job is None or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        archive = build_project_archive(service().root, composition_id, version)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FileResponse(
        archive, media_type="application/zip", filename=f"whispers-v{version}.zip"
    )


@app.get("/api/v1/preferences")
def preferences() -> dict:
    return recommend_moods(service().root)


@app.post("/api/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    manager = service()
    job = manager.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["state"] != "awaiting_cloud":
        raise HTTPException(
            status_code=409, detail="Only not-yet-imported cloud jobs may be cancelled"
        )
    manager.jobs.save(
        job_id, state="cancelled", provider=job["provider"],
        request_id=job["request_id"], data={"reason": "Cancelled by user"},
    )
    return manager.jobs.get(job_id)

class FavoriteRequest(BaseModel):
    favorite: bool = True


class PlaylistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PlaylistItemRequest(BaseModel):
    composition_id: str = Field(min_length=1, max_length=64)


class SettingsRequest(BaseModel):
    default_genre: Literal[
        "cinematic", "ambient", "classical", "electronic", "jazz"
    ] = "cinematic"
    default_tempo: int = Field(default=96, ge=60, le=160)
    listen_volume: int = Field(default=80, ge=0, le=100)
    default_provider: Literal["rule_based", "midigpt"] = "rule_based"


@app.get("/api/v1/library")
def library(limit: int = Query(default=100, ge=1, le=250)) -> dict:
    store = service()
    starred = LibraryStore(store.root).favorites()
    results = []
    for job in store.jobs.list_jobs(limit=limit):
        bp_path = store.root / "artifacts" / job["job_id"] / "blueprint.json"
        if not bp_path.is_file():
            continue
        try:
            bp = MusicBlueprint.model_validate_json(
                bp_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            continue
        results.append({
            **job, "prompt": bp.prompt, "genre": bp.genre,
            "tempo_bpm": bp.tempo_bpm, "bars": bp.total_bars,
            "moods": [s.mood for s in bp.sections],
            "favorite": job["job_id"] in starred,
        })
    return {"items": results, "count": len(results)}


@app.put("/api/v1/library/{composition_id}/favorite")
def set_favorite(composition_id: str, request: FavoriteRequest) -> dict:
    job = service().jobs.get(composition_id)
    if not job or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Completed composition not found")
    return LibraryStore(service().root).favorite(composition_id, request.favorite)


@app.get("/api/v1/playlists")
def playlists() -> dict:
    return {"items": LibraryStore(service().root).playlists()}


@app.post("/api/v1/playlists", status_code=201)
def create_playlist(request: PlaylistCreateRequest) -> dict:
    return LibraryStore(service().root).create_playlist(request.name)


@app.post("/api/v1/playlists/{playlist_id}/items")
def playlist_add_item(playlist_id: str, request: PlaylistItemRequest) -> dict:
    job = service().jobs.get(request.composition_id)
    if not job or job["state"] != "completed":
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        LibraryStore(service().root).add_item(playlist_id, request.composition_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"playlist_id": playlist_id, "composition_id": request.composition_id}


@app.delete("/api/v1/playlists/{playlist_id}/items/{composition_id}")
def playlist_remove_item(playlist_id: str, composition_id: str) -> dict:
    try:
        LibraryStore(service().root).remove_item(playlist_id, composition_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"playlist_id": playlist_id, "composition_id": composition_id, "removed": True}


@app.get("/api/v1/settings")
def get_settings() -> dict:
    return LibraryStore(service().root).settings()


@app.put("/api/v1/settings")
def update_settings(request: SettingsRequest) -> dict:
    return LibraryStore(service().root).save_settings(request.model_dump())


@app.get("/api/v1/compositions/{composition_id}/blueprint",
         response_model=MusicBlueprint)
def get_composition_blueprint(composition_id: str) -> MusicBlueprint:
    job = service().jobs.get(composition_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Composition not found")
    try:
        path = version_directory(service().root, composition_id, 1) / "blueprint.json"
        return MusicBlueprint.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class BatchRequest(BaseModel):
    blueprints: list[MusicBlueprint] = Field(min_length=1, max_length=4)


@app.post("/api/v1/jobs/batch", status_code=202)
def generate_batch(request: BatchRequest) -> dict:
    # CPU batches are deliberately capped; Kaggle requests remain asynchronous.
    results = [service().create(blueprint) for blueprint in request.blueprints]
    return {"jobs": results, "count": len(results)}


@app.post("/api/v1/compositions/{composition_id}/variations", status_code=202)
def create_variation(composition_id: str, request: VariationRequest) -> dict:
    manager = service()
    current = manager.jobs.get(composition_id)
    if current is None or current["state"] != "completed":
        raise HTTPException(status_code=404, detail="Original composition not found")
    try:
        from wow.editing import version_directory
        path = version_directory(manager.root, composition_id, 1) / "blueprint.json"
        blueprint = MusicBlueprint.model_validate_json(path.read_text(encoding="utf-8"))
        proposed = vary(blueprint, request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    job = manager.create(proposed)
    return {**job, "source_composition_id": composition_id}


class ContextAnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    activity: str | None = Field(default=None, max_length=40)
    weather: str | None = Field(default=None, max_length=40)
    time_of_day: str | None = Field(default=None, max_length=40)


@app.post("/api/v1/context")
def context_analysis(request: ContextAnalyzeRequest) -> dict:
    signals = extract_context(
        request.prompt, activity=request.activity, weather=request.weather,
        time_of_day=request.time_of_day,
    )
    return {
        "context": signals.model_dump(),
        "method": "keyword_matching_with_explicit_user_override",
        "limitation": "No physical sensors, location services or weather APIs are used",
    }

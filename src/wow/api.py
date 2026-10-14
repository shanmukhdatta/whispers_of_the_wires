"""Phase 1 HTTP contract. GPU-backed job endpoints arrive in subsequent phases."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from wow.contracts import MusicBlueprint, default_blueprint

app = FastAPI(title="Whispers of the Wires API", version="0.1.0")


class PlanRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    request_id: str = Field(default="demo-001", min_length=1, max_length=100)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/v1/blueprints", response_model=MusicBlueprint)
def create_blueprint(request: PlanRequest) -> MusicBlueprint:
    # Phase 1: intentionally static emotional sections. Phase 2 replaces this.
    return default_blueprint(request.prompt, request.request_id)

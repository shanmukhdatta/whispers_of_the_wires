"""Create reversible new compositions without silently altering saved versions."""
from __future__ import annotations

from pydantic import BaseModel, Field

from wow.contracts import MusicBlueprint


class VariationRequest(BaseModel):
    seed: int = Field(ge=0, le=2**32 - 1)
    extend_bars: int = Field(default=0, ge=0, le=16)


def vary(original: MusicBlueprint, request: VariationRequest) -> MusicBlueprint:
    result = original.model_copy(deep=True)
    result.generation.seed = request.seed
    if request.extend_bars:
        if result.total_bars + request.extend_bars > 64:
            raise ValueError("Maximum composition is 64 bars")
        result.sections[-1].bar_count += request.extend_bars
        result.total_bars += request.extend_bars
    # A new job has a different request ID, but the parent remains traceable.
    import uuid
    result.request_id = str(uuid.uuid4())
    return MusicBlueprint.model_validate(result.model_dump())

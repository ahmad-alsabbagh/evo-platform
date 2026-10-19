from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvaluationRunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=256)
    schema_version: str
    capability_id: str
    capability_version: str
    dataset_id: str
    dataset_version: str
    dataset_hash: str
    status: str
    promotion: str
    payload: dict[str, Any]


class EvaluationRunView(EvaluationRunInput):
    created_at: str
    completed_at: str | None = None
    created_by: str | None = None

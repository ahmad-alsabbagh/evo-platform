from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high", "critical"]


class PromotionState(StrEnum):
    blocked = "blocked"
    candidate = "candidate"
    canary = "canary"
    promoted = "promoted"
    rejected = "rejected"
    revoked = "revoked"
    rolled_back = "rolled_back"


class CatalogQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation_status: Literal["not-run", "passed", "failed", "stale"]
    score: float | None = Field(default=None, ge=0, le=1)
    reproducibility: float | None = Field(default=None, ge=0, le=1)
    trust: float | None = Field(default=None, ge=0, le=1)
    regression_status: Literal["not-run", "passed", "failed"] = "not-run"


class CatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=256)
    capability_id: str
    capability_version: str
    risk_level: RiskLevel
    quality: CatalogQuality
    license_identifier: str | None = None
    provenance_source_type: str | None = None
    human_reviewed: bool = False
    artifact_digest: str | None = None


class PromotionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=256)
    state: PromotionState
    reasons: list[str]
    policy_version: str
    policy_snapshot_hash: str | None = None
    evaluation_run_id: str | None = None
    actor: str | None = None
    artifact_digest: str | None = None

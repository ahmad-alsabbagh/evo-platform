from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["low", "medium", "high", "critical"]


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


class PromotionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    target_lifecycle: Literal["candidate", "canary", "promoted", "rejected"]
    reasons: list[str]
    policy_version: str

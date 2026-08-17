from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_platform.catalog.models import CatalogEntry, PromotionDecision, PromotionState
from evo_platform.storage.models import CatalogEntryRecord, PromotionDecisionRecord, EvaluationRun


class CatalogRepository(Protocol):
    async def publish_if_promoted(self, entry: CatalogEntry, decision: PromotionDecision) -> CatalogEntry: ...
    async def get(self, entry_id: str) -> CatalogEntry | None: ...
    async def list_published(self, limit: int = 100) -> Sequence[CatalogEntryRecord]: ...


class SqlAlchemyCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def publish_if_promoted(self, entry: CatalogEntry, decision: PromotionDecision) -> CatalogEntry:
        if decision.state != PromotionState.promoted:
            raise ValueError("catalog publication requires a promoted decision")
        if decision.evaluation_run_id is None:
            raise ValueError("catalog publication requires evaluation_run_id")
        evaluation = await self.session.get(EvaluationRun, decision.evaluation_run_id)
        if evaluation is None:
            raise ValueError("evaluation_run_not_found")
        if evaluation.capability_id != entry.capability_id or evaluation.capability_version != entry.capability_version:
            raise ValueError("evaluation_capability_mismatch")
        if decision.artifact_digest and entry.artifact_digest and decision.artifact_digest != entry.artifact_digest:
            raise ValueError("artifact_digest_mismatch")
        existing = await self.session.get(PromotionDecisionRecord, str(decision.decision_id))
        if existing is not None:
            return entry
        record = CatalogEntryRecord(
            id=entry.id,
            capability_id=entry.capability_id,
            capability_version=entry.capability_version,
            lifecycle=decision.state.value,
            risk_level=entry.risk_level,
            payload=entry.model_dump(mode="json"),
        )
        audit = PromotionDecisionRecord(
            id=str(decision.decision_id),
            catalog_entry_id=entry.id,
            evaluation_run_id=decision.evaluation_run_id,
            state=decision.state.value,
            policy_version=decision.policy_version,
            policy_snapshot_hash=decision.policy_snapshot_hash,
            idempotency_key=decision.idempotency_key,
            reasons=decision.reasons,
            actor=decision.actor,
            artifact_digest=decision.artifact_digest or entry.artifact_digest,
        )
        self.session.add(record)
        self.session.add(audit)
        await self.session.flush()
        return entry

    async def get(self, entry_id: str) -> CatalogEntry | None:
        record = await self.session.get(CatalogEntryRecord, entry_id)
        if record is None:
            return None
        return CatalogEntry.model_validate(record.payload)

    async def list_published(self, limit: int = 100) -> Sequence[CatalogEntryRecord]:
        result = await self.session.execute(
            select(CatalogEntryRecord)
            .where(CatalogEntryRecord.lifecycle == PromotionState.promoted.value)
            .order_by(CatalogEntryRecord.published_at.desc())
            .limit(max(1, min(limit, 1000)))
        )
        return result.scalars().all()

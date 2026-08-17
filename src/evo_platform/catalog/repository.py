from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_platform.catalog.models import CatalogEntry, PromotionDecision
from evo_platform.storage.models import CatalogEntryRecord, PromotionDecisionRecord


class CatalogRepository(Protocol):
    async def publish_if_promoted(
        self,
        entry: CatalogEntry,
        decision: PromotionDecision,
    ) -> CatalogEntry: ...

    async def get(self, entry_id: str) -> CatalogEntry | None: ...
    async def list_published(self, limit: int = 100) -> Sequence[CatalogEntryRecord]: ...


class SqlAlchemyCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def publish_if_promoted(self, entry: CatalogEntry, decision: PromotionDecision) -> CatalogEntry:
        if not decision.allowed or decision.target_lifecycle != "promoted":
            raise ValueError("catalog publication requires an allowed promoted decision")
        if decision.evaluation_run_id is None:
            raise ValueError("catalog publication requires evaluation_run_id")
        record = CatalogEntryRecord(
            id=entry.id,
            capability_id=entry.capability_id,
            capability_version=entry.capability_version,
            lifecycle="promoted",
            risk_level=entry.risk_level,
            payload=entry.model_dump(mode="json"),
        )
        audit = PromotionDecisionRecord(
            id=f"decision:{entry.id}:{decision.policy_version}",
            catalog_entry_id=entry.id,
            evaluation_run_id=decision.evaluation_run_id,
            allowed=decision.allowed,
            target_lifecycle=decision.target_lifecycle,
            policy_version=decision.policy_version,
            policy_snapshot_hash=decision.policy_snapshot_hash,
            reasons=decision.reasons,
            actor=decision.actor,
            artifact_digest=entry.artifact_digest,
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
            .where(CatalogEntryRecord.lifecycle == "promoted")
            .order_by(CatalogEntryRecord.published_at.desc())
            .limit(max(1, min(limit, 1000)))
        )
        return result.scalars().all()

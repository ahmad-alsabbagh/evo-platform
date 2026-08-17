from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_platform.catalog.models import CatalogEntry
from evo_platform.storage.models import CatalogEntryRecord, PromotionDecisionRecord


class CatalogRepository(Protocol):
    async def publish(self, entry: CatalogEntry) -> CatalogEntry: ...
    async def get(self, entry_id: str) -> CatalogEntry | None: ...
    async def list_published(self, limit: int = 100) -> Sequence[CatalogEntryRecord]: ...
    async def record_decision(self, entry_id: str, decision_id: str, allowed: bool, target_lifecycle: str, policy_version: str, reasons: list[str]) -> None: ...


class SqlAlchemyCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def publish(self, entry: CatalogEntry) -> CatalogEntry:
        record = CatalogEntryRecord(
            id=entry.id,
            capability_id=entry.capability_id,
            capability_version=entry.capability_version,
            lifecycle="promoted",
            risk_level=entry.risk_level,
            payload=entry.model_dump(mode="json"),
        )
        self.session.add(record)
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

    async def record_decision(
        self,
        entry_id: str,
        decision_id: str,
        allowed: bool,
        target_lifecycle: str,
        policy_version: str,
        reasons: list[str],
    ) -> None:
        self.session.add(
            PromotionDecisionRecord(
                id=decision_id,
                catalog_entry_id=entry_id,
                allowed=allowed,
                target_lifecycle=target_lifecycle,
                policy_version=policy_version,
                reasons=reasons,
            )
        )
        await self.session.flush()

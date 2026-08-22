from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from evo_platform.domain.evaluation import EvaluationRunInput
from evo_platform.storage.models import EvaluationRun


class EvaluationRunRepository(Protocol):
    async def create(
        self, value: EvaluationRunInput, *, created_by: str | None = None
    ) -> EvaluationRun: ...
    async def get(self, run_id: str) -> EvaluationRun | None: ...
    async def list_for_capability(
        self, capability_id: str, limit: int = 100
    ) -> Sequence[EvaluationRun]: ...


class SqlAlchemyEvaluationRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, value: EvaluationRunInput, *, created_by: str | None = None
    ) -> EvaluationRun:
        record = EvaluationRun(
            id=value.id,
            schema_version=value.schema_version,
            capability_id=value.capability_id,
            capability_version=value.capability_version,
            dataset_id=value.dataset_id,
            dataset_version=value.dataset_version,
            dataset_hash=value.dataset_hash,
            status=value.status,
            promotion=value.promotion,
            payload=value.payload,
            created_by=created_by,
        )
        self.session.add(record)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            existing = await self.get(value.id)
            if existing is not None:
                return existing
            raise
        return record

    async def get(self, run_id: str) -> EvaluationRun | None:
        return await self.session.get(EvaluationRun, run_id)

    async def list_for_capability(
        self, capability_id: str, limit: int = 100
    ) -> Sequence[EvaluationRun]:
        bounded_limit = max(1, min(limit, 1000))
        result = await self.session.execute(
            select(EvaluationRun)
            .where(EvaluationRun.capability_id == capability_id)
            .order_by(EvaluationRun.created_at.desc())
            .limit(bounded_limit)
        )
        return result.scalars().all()

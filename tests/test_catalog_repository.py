from unittest.mock import AsyncMock

import pytest

from evo_platform.catalog.models import CatalogEntry
from evo_platform.catalog.repository import SqlAlchemyCatalogRepository


@pytest.fixture
def entry() -> CatalogEntry:
    return CatalogEntry(
        id="catalog:summarize",
        capability_id="summarize",
        capability_version="1.0.0",
        risk_level="low",
        quality={"evaluation_status": "passed", "score": 0.95, "reproducibility": 0.95, "trust": 0.9, "regression_status": "passed"},
        license_identifier="Apache-2.0",
        provenance_source_type="original",
    )


@pytest.mark.asyncio
async def test_publish_adds_record(entry: CatalogEntry) -> None:
    session = AsyncMock()
    repository = SqlAlchemyCatalogRepository(session)

    result = await repository.publish(entry)

    assert result.id == entry.id
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_decision_persists_reasons() -> None:
    session = AsyncMock()
    repository = SqlAlchemyCatalogRepository(session)

    await repository.record_decision("catalog:summarize", "decision:1", False, "rejected", "1.0.0", ["regression_not_passed"])

    record = session.add.call_args.args[0]
    assert record.reasons == ["regression_not_passed"]
    assert record.policy_version == "1.0.0"
    session.flush.assert_awaited_once()

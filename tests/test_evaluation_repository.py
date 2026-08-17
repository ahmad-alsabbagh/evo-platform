from unittest.mock import AsyncMock, Mock

import pytest

from evo_platform.domain.evaluation import EvaluationRunInput
from evo_platform.storage.repositories import SqlAlchemyEvaluationRunRepository


@pytest.fixture
def value() -> EvaluationRunInput:
    return EvaluationRunInput(
        id="eval-run:001",
        schema_version="1.0.0",
        capability_id="summarize",
        capability_version="1.0.0",
        dataset_id="golden",
        dataset_version="1.0.0",
        dataset_hash="sha256:" + "a" * 64,
        status="completed",
        promotion="candidate",
        payload={"metrics": {"accuracy": 0.9}},
    )


@pytest.mark.asyncio
async def test_create_adds_record(value: EvaluationRunInput) -> None:
    session = AsyncMock()
    repository = SqlAlchemyEvaluationRunRepository(session)

    result = await repository.create(value, created_by="test")

    assert result.id == value.id
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_uses_primary_key() -> None:
    session = AsyncMock()
    repository = SqlAlchemyEvaluationRunRepository(session)
    expected = Mock()
    session.get.return_value = expected

    result = await repository.get("eval-run:001")

    assert result is expected
    session.get.assert_awaited_once()

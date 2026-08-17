import pytest
from sqlalchemy import text

from evo_platform.domain.evaluation import EvaluationRunInput
from evo_platform.storage.repositories import SqlAlchemyEvaluationRunRepository


def value(run_id: str = "eval-run:integration") -> EvaluationRunInput:
    return EvaluationRunInput(
        id=run_id,
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


@pytest.mark.integration
async def test_repository_round_trip(session) -> None:
    repository = SqlAlchemyEvaluationRunRepository(session)
    await repository.create(value())
    await session.commit()

    result = await repository.get("eval-run:integration")
    assert result is not None
    assert result.dataset_hash == "sha256:" + "a" * 64


@pytest.mark.integration
async def test_transaction_rollback(session) -> None:
    repository = SqlAlchemyEvaluationRunRepository(session)
    await repository.create(value("eval-run:rollback"))
    await session.rollback()

    result = await repository.get("eval-run:rollback")
    assert result is None


@pytest.mark.integration
async def test_migration_table(session) -> None:
    result = await session.execute(text("SELECT version_num FROM alembic_version"))
    assert result.scalar_one() == "0001_create_evaluation_runs"

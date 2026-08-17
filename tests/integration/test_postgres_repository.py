import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from evo_platform.domain.evaluation import EvaluationRunInput
from evo_platform.storage.models import Base
from evo_platform.storage.repositories import SqlAlchemyEvaluationRunRepository


@pytest.fixture
async def session():
    engine = create_async_engine("postgresql+asyncpg://evo:evo@localhost:5432/evo")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


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
async def test_health_query(session) -> None:
    result = await session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1

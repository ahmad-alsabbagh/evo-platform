import os
import subprocess

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def session() -> AsyncSession:
    database_url = os.environ["EVO_DATABASE_URL"]
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=os.environ.copy())
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: sync_connection.exec_driver_sql(
                "TRUNCATE promotion_decisions, catalog_entries, evaluation_runs CASCADE"
            )
        )
    subprocess.run(["alembic", "downgrade", "base"], check=True, env=os.environ.copy())
    await engine.dispose()

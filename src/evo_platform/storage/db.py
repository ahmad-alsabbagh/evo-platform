from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from evo_platform.config import get_settings


DEFAULT_POOL_SIZE: Final = 5
DEFAULT_MAX_OVERFLOW: Final = 10


def database_url() -> str:
    return get_settings().database_url


def create_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(
        url or database_url(),
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
    )


engine = create_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession] = SessionFactory,
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

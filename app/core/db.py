from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings, normalize_database_url

async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db_engine(database_url: str | None = None) -> None:
    global async_session_factory
    settings = get_settings()
    resolved_database_url = normalize_database_url(database_url) if database_url else settings.database_url
    engine = create_async_engine(resolved_database_url, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_db_engine() -> None:
    global async_session_factory
    if async_session_factory is None:
        return
    await async_session_factory.kw["bind"].dispose()
    async_session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        init_db_engine()
    assert async_session_factory is not None
    async with async_session_factory() as session:
        yield session

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import build_database_engine_config, get_settings

async_session_factory: async_sessionmaker[AsyncSession] | None = None
engine_connect_args: dict[str, Any] = {}
REQUIRED_SCHEMA_TABLES = (
    "drivers",
    "driver_identities",
    "refresh_tokens",
    "trips",
    "trip_points",
    "media_objects",
    "sticker_submissions",
    "odometer_submissions",
)


class SchemaNotReadyError(RuntimeError):
    pass


def init_db_engine(database_url: str | None = None) -> None:
    global async_session_factory, engine_connect_args
    settings = get_settings()
    resolved_database_url, engine_connect_args = build_database_engine_config(
        database_url or settings.database_url
    )
    engine = create_async_engine(
        resolved_database_url,
        pool_pre_ping=True,
        connect_args=engine_connect_args,
    )
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_db_engine() -> None:
    global async_session_factory, engine_connect_args
    if async_session_factory is None:
        return
    await async_session_factory.kw["bind"].dispose()
    async_session_factory = None
    engine_connect_args = {}


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        init_db_engine()
    assert async_session_factory is not None
    async with async_session_factory() as session:
        yield session


def _missing_required_tables(sync_connection) -> tuple[str, ...]:
    inspector = inspect(sync_connection)
    return tuple(table for table in REQUIRED_SCHEMA_TABLES if not inspector.has_table(table))


async def ensure_schema_ready(session: AsyncSession) -> None:
    connection = await session.connection()
    missing_tables = await connection.run_sync(_missing_required_tables)
    if missing_tables:
        raise SchemaNotReadyError(
            "Database schema is not ready. Missing tables: "
            f"{', '.join(missing_tables)}. Run `python -m alembic upgrade head`."
        )

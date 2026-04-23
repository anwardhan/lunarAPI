from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import SchemaNotReadyError, ensure_schema_ready
from app.models import Base


@pytest.mark.asyncio
async def test_schema_ready_passes_when_required_tables_exist(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ready.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        await ensure_schema_ready(session)

    await engine.dispose()


@pytest.mark.asyncio
async def test_schema_ready_fails_when_tables_are_missing(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'missing.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        with pytest.raises(SchemaNotReadyError, match="driver_identities"):
            await ensure_schema_ready(session)

    await engine.dispose()

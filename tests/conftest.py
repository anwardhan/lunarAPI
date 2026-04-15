from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import db
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
async def test_database(tmp_path) -> AsyncGenerator[None, None]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'lunar_test.db'}")
    db.async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    db.async_session_factory = None


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as http:
        yield http


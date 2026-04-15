from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import auth, drivers, media, submissions, trips
from app.core.db import dispose_db_engine, get_session, init_db_engine
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db_engine()
    yield
    await dispose_db_engine()


app = FastAPI(
    title="Lunar Car API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    async for session in get_session():
        await session.execute(text("select 1"))
        break
    return {"status": "ready"}


for api_router in (auth.router, drivers.router, trips.router, media.router, submissions.router):
    app.include_router(api_router, prefix="/v1")
    app.include_router(api_router)


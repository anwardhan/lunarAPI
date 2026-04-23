from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import auth, drivers, media, submissions, trips
from app.core.db import (
    SchemaNotReadyError,
    dispose_db_engine,
    ensure_schema_ready,
    get_session,
    init_db_engine,
)
from app.core.logging import configure_logging
from app.portal import STATIC_DIR as PORTAL_STATIC_DIR
from app.portal import router as portal_router


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

app.mount("/portal/assets", StaticFiles(directory=PORTAL_STATIC_DIR), name="portal-assets")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    async for session in get_session():
        await session.execute(text("select 1"))
        try:
            await ensure_schema_ready(session)
        except SchemaNotReadyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        break
    return {"status": "ready"}


for api_router in (auth.router, drivers.router, trips.router, media.router, submissions.router):
    app.include_router(api_router, prefix="/v1")
    app.include_router(api_router)

app.include_router(portal_router)

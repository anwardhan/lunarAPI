from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import decode_token
from app.models.driver import Driver
from app.services.driver_service import DriverService

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_driver(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Driver:
    payload = decode_token(credentials.credentials, expected_type="access")
    return await DriverService(session).get_by_driver_id(str(payload["sub"]))


CurrentDriver = Annotated[Driver, Depends(get_current_driver)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


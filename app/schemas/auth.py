from __future__ import annotations

from app.schemas.common import APIModel
from app.schemas.driver import DriverResponse


class ProviderLoginRequest(APIModel):
    identity_token: str


class AuthSessionResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    driver: DriverResponse


class RefreshRequest(APIModel):
    refresh_token: str


class RefreshResponse(APIModel):
    access_token: str
    token_type: str = "bearer"


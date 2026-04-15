from __future__ import annotations

from fastapi import APIRouter

from app.api.deps.auth import DbSession
from app.schemas.auth import AuthSessionResponse, ProviderLoginRequest, RefreshRequest, RefreshResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/auth/apple/login", response_model=AuthSessionResponse)
@router.post("/auth/apple", response_model=AuthSessionResponse)
async def login_with_apple(request: ProviderLoginRequest, session: DbSession) -> AuthSessionResponse:
    return await AuthService(session).login_with_provider("apple", request.identity_token)


@router.post("/auth/google/login", response_model=AuthSessionResponse)
@router.post("/auth/google", response_model=AuthSessionResponse)
async def login_with_google(request: ProviderLoginRequest, session: DbSession) -> AuthSessionResponse:
    return await AuthService(session).login_with_provider("google", request.identity_token)


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest, session: DbSession) -> RefreshResponse:
    return await AuthService(session).refresh_access_token(request.refresh_token)


from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.deps.auth import DbSession
from app.core.config import Settings, get_settings
from app.core.security import create_portal_session_token, decode_token, verify_portal_password
from app.schemas.portal import (
    PortalDashboardResponse,
    PortalLoginRequest,
    PortalSessionResponse,
    PortalTripDetailResponse,
)
from app.services.portal_service import PortalService

router = APIRouter(prefix="/portal", tags=["portal"])
STATIC_DIR = Path(__file__).resolve().parent / "static"
SESSION_COOKIE_NAME = "lunar_portal_session"


def _ensure_portal_configured(settings: Settings) -> None:
    if not settings.portal_admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Portal is not configured. Set PORTAL_ADMIN_PASSWORD first.",
        )


def _cookie_secure(request: Request, settings: Settings) -> bool:
    return request.url.scheme == "https" or settings.api_base_url.startswith("https://")


def require_portal_session(request: Request) -> dict[str, str | int]:
    settings = get_settings()
    _ensure_portal_configured(settings)
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Portal login required",
        )
    return decode_token(token, expected_type="portal")


@router.get("", include_in_schema=False)
async def portal_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.post("/login", response_model=PortalSessionResponse)
async def portal_login(request: PortalLoginRequest, raw_request: Request) -> JSONResponse:
    settings = get_settings()
    _ensure_portal_configured(settings)
    if not verify_portal_password(request.password, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid portal password")

    token = create_portal_session_token(settings)
    response = JSONResponse(PortalSessionResponse().model_dump(mode="json"))
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(raw_request, settings),
        max_age=settings.portal_session_hours * 3600,
        path="/portal",
    )
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def portal_logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/portal")
    return response


@router.get("/api/session", response_model=PortalSessionResponse)
async def portal_session(_payload: dict[str, str | int] = Depends(require_portal_session)) -> PortalSessionResponse:
    return PortalSessionResponse()


@router.get("/api/dashboard", response_model=PortalDashboardResponse)
async def portal_dashboard(
    session: DbSession,
    _payload: dict[str, str | int] = Depends(require_portal_session),
) -> PortalDashboardResponse:
    return await PortalService(session).get_dashboard()


@router.get("/api/trips/{trip_id}", response_model=PortalTripDetailResponse)
async def portal_trip_detail(
    trip_id: str,
    session: DbSession,
    _payload: dict[str, str | int] = Depends(require_portal_session),
) -> PortalTripDetailResponse:
    return await PortalService(session).get_trip_detail(trip_id)


@router.get("/media/{kind}/{submission_id}", include_in_schema=False)
async def portal_media(
    kind: str,
    submission_id: str,
    session: DbSession,
    _payload: dict[str, str | int] = Depends(require_portal_session),
) -> FileResponse:
    path, media_type = await PortalService(session).get_media_file(kind, submission_id)
    return FileResponse(path, media_type=media_type)

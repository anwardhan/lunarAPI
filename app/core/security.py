from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.ids import public_id
from app.core.time import utc_now


def hash_token(value: str) -> str:
    secret = get_settings().jwt_secret.encode("utf-8")
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_access_token(driver_id: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = utc_now()
    payload: dict[str, Any] = {
        "sub": driver_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(driver_id: str, settings: Settings | None = None) -> tuple[str, str]:
    settings = settings or get_settings()
    now = utc_now()
    jti = public_id("rt")
    payload: dict[str, Any] = {
        "sub": driver_id,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_token_days)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


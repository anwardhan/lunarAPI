from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.ids import public_id
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.core.time import utc_now
from app.models.driver import Driver, DriverIdentity, RefreshToken
from app.schemas.auth import AuthSessionResponse, RefreshResponse
from app.schemas.driver import DriverResponse
from app.services.audit_service import record_audit_event


@dataclass(frozen=True)
class ProviderIdentity:
    provider: str
    subject_id: str
    email: str | None
    display_name: str | None
    email_verified: bool = False


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def login_with_provider(self, provider: str, identity_token: str) -> AuthSessionResponse:
        identity = self.verify_provider_token(provider, identity_token)
        now = utc_now()

        identity_stmt = select(DriverIdentity).where(
            DriverIdentity.provider == provider,
            DriverIdentity.provider_subject_id == identity.subject_id,
        )
        existing_identity = (await self.session.execute(identity_stmt)).scalar_one_or_none()

        if existing_identity is not None:
            driver = await self.session.get(Driver, existing_identity.driver_fk)
            if driver is None:
                raise HTTPException(status_code=500, detail="Identity is missing driver")
            existing_identity.provider_email = identity.email
            existing_identity.last_used_at = now
            driver.last_login_at = now
            driver.updated_at = now
        else:
            driver = Driver(
                driver_id=public_id("drv"),
                primary_email=identity.email,
                email_verified=identity.email_verified,
                full_name=identity.display_name,
                status="active",
                created_at=now,
                updated_at=now,
                last_login_at=now,
            )
            self.session.add(driver)
            await self.session.flush()
            self.session.add(
                DriverIdentity(
                    driver_fk=driver.id,
                    provider=provider,
                    provider_subject_id=identity.subject_id,
                    provider_email=identity.email,
                    created_at=now,
                    last_used_at=now,
                )
            )

        access_token = create_access_token(driver.driver_id)
        refresh_token, refresh_jti = create_refresh_token(driver.driver_id)
        self.session.add(
            RefreshToken(
                driver_fk=driver.id,
                jti_hash=hash_token(refresh_jti),
                expires_at=now + timedelta(days=self.settings.jwt_refresh_token_days),
                created_at=now,
            )
        )
        await record_audit_event(
            self.session,
            event_type="auth.login_success",
            driver_id=driver.driver_id,
            metadata={"provider": provider},
        )
        await self.session.commit()
        await self.session.refresh(driver)

        return AuthSessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            driver=self.to_driver_response(driver),
        )

    async def refresh_access_token(self, refresh_token: str) -> RefreshResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        driver_id = str(payload["sub"])
        jti = str(payload["jti"])

        driver = (
            await self.session.execute(select(Driver).where(Driver.driver_id == driver_id))
        ).scalar_one_or_none()
        if driver is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown driver")

        stored_token = (
            await self.session.execute(
                select(RefreshToken).where(
                    RefreshToken.driver_fk == driver.id,
                    RefreshToken.jti_hash == hash_token(jti),
                    RefreshToken.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if stored_token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh expired")
        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh expired")

        await record_audit_event(
            self.session,
            event_type="auth.refresh_success",
            driver_id=driver.driver_id,
        )
        await self.session.commit()
        return RefreshResponse(access_token=create_access_token(driver.driver_id))

    def verify_provider_token(self, provider: str, identity_token: str) -> ProviderIdentity:
        if not identity_token.strip():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

        if self.settings.auth_provider_verification == "development":
            digest = hashlib.sha256(identity_token.encode("utf-8")).hexdigest()
            email = identity_token if "@" in identity_token and " " not in identity_token else None
            return ProviderIdentity(
                provider=provider,
                subject_id=f"dev:{digest[:32]}",
                email=email or f"{provider}-{digest[:10]}@example.test",
                display_name=f"{provider.title()} Driver",
                email_verified=email is not None,
            )

        # Production integration point. Apple and Google verification should validate issuer,
        # audience/client ID, signature, nonce where applicable, and expiration before returning.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider} provider verification is not configured",
        )

    @staticmethod
    def to_driver_response(driver: Driver) -> DriverResponse:
        return DriverResponse(
            driver_id=driver.driver_id,
            email=driver.primary_email,
            display_name=driver.full_name,
            created_at=driver.created_at,
        )

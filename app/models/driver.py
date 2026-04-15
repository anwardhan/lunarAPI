from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import uuid_str
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.media import MediaObject
    from app.models.submission import OdometerSubmission, StickerSubmission
    from app.models.trip import Trip


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    driver_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    primary_email: Mapped[str | None] = mapped_column(String(320), index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    identities: Mapped[list[DriverIdentity]] = relationship(back_populates="driver")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="driver")
    trips: Mapped[list[Trip]] = relationship(back_populates="driver")
    media_objects: Mapped[list[MediaObject]] = relationship(back_populates="driver")
    sticker_submissions: Mapped[list[StickerSubmission]] = relationship(back_populates="driver")
    odometer_submissions: Mapped[list[OdometerSubmission]] = relationship(back_populates="driver")


class DriverIdentity(Base):
    __tablename__ = "driver_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject_id", name="uq_driver_identity_provider"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_subject_id: Mapped[str] = mapped_column(String(256), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(320))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    driver: Mapped[Driver] = relationship(back_populates="identities")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    jti_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    driver: Mapped[Driver] = relationship(back_populates="refresh_tokens")


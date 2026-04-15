from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import uuid_str
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.submission import OdometerSubmission, StickerSubmission


class MediaObject(Base):
    __tablename__ = "media_objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    media_id: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(120), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    original_file_name: Mapped[str | None] = mapped_column(String(255))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending_upload", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    driver: Mapped[Driver] = relationship(back_populates="media_objects")
    sticker_submissions: Mapped[list[StickerSubmission]] = relationship(back_populates="media_object")
    odometer_submissions: Mapped[list[OdometerSubmission]] = relationship(back_populates="media_object")


from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import uuid_str
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.media import MediaObject
    from app.models.trip import Trip


class StickerSubmission(Base):
    __tablename__ = "sticker_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    submission_id: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    media_object_fk: Mapped[str] = mapped_column(ForeignKey("media_objects.id"), nullable=False)
    trip_fk: Mapped[str | None] = mapped_column(ForeignKey("trips.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gps_lat: Mapped[float | None] = mapped_column(Float)
    gps_lng: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(32), default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    driver: Mapped[Driver] = relationship(back_populates="sticker_submissions")
    media_object: Mapped[MediaObject] = relationship(back_populates="sticker_submissions")


class OdometerSubmission(Base):
    __tablename__ = "odometer_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    submission_id: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    media_object_fk: Mapped[str] = mapped_column(ForeignKey("media_objects.id"), nullable=False)
    trip_fk: Mapped[str | None] = mapped_column(ForeignKey("trips.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gps_lat: Mapped[float | None] = mapped_column(Float)
    gps_lng: Mapped[float | None] = mapped_column(Float)
    ocr_value: Mapped[int | None] = mapped_column(Integer)
    ocr_confidence: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(32), default="pending_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    driver: Mapped[Driver] = relationship(back_populates="odometer_submissions")
    media_object: Mapped[MediaObject] = relationship(back_populates="odometer_submissions")


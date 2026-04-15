from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import uuid_str
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        UniqueConstraint("driver_fk", "client_trip_id", name="uq_trips_driver_client_trip"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    trip_id: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    driver_fk: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    client_trip_id: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_lat: Mapped[float | None] = mapped_column(Float)
    start_lng: Mapped[float | None] = mapped_column(Float)
    end_lat: Mapped[float | None] = mapped_column(Float)
    end_lng: Mapped[float | None] = mapped_column(Float)
    device_platform: Mapped[str | None] = mapped_column(String(32))
    app_version: Mapped[str | None] = mapped_column(String(32))
    os_version: Mapped[str | None] = mapped_column(String(32))
    device_distance_meters: Mapped[float | None] = mapped_column(Float)
    total_distance_meters: Mapped[float | None] = mapped_column(Float)
    point_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    driver: Mapped[Driver] = relationship(back_populates="trips")
    points: Mapped[list[TripPoint]] = relationship(back_populates="trip")
    batches: Mapped[list[TripPointBatch]] = relationship(back_populates="trip")


class TripPointBatch(Base):
    __tablename__ = "trip_point_batches"
    __table_args__ = (
        UniqueConstraint("trip_fk", "batch_id", name="uq_trip_point_batches_trip_batch"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    trip_fk: Mapped[str] = mapped_column(ForeignKey("trips.id"), nullable=False)
    batch_id: Mapped[str] = mapped_column(String(120), nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    trip: Mapped[Trip] = relationship(back_populates="batches")


class TripPoint(Base):
    __tablename__ = "trip_points"
    __table_args__ = (
        UniqueConstraint(
            "trip_fk",
            "recorded_at",
            "latitude",
            "longitude",
            name="uq_trip_points_trip_time_location",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    trip_fk: Mapped[str] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    horizontal_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    vertical_accuracy: Mapped[float | None] = mapped_column(Float)
    speed_mps: Mapped[float | None] = mapped_column(Float)
    course_degrees: Mapped[float | None] = mapped_column(Float)
    altitude_meters: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64), default="ios_corelocation", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    trip: Mapped[Trip] = relationship(back_populates="points")

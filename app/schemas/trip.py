from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import APIModel, Coordinates, DeviceInfo


class StartTripRequest(APIModel):
    started_at: datetime | None = None
    device: DeviceInfo | None = None
    start_location: Coordinates | None = None
    client_trip_id: str | None = None


class TripResponse(APIModel):
    trip_id: str
    driver_id: str
    started_at: datetime
    status: str
    ended_at: datetime | None = None


class TripPointIn(APIModel):
    timestamp: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    horizontal_accuracy: float = Field(ge=0)
    vertical_accuracy: float | None = None
    speed_mps: float | None = None
    course_degrees: float | None = None
    altitude_meters: float | None = None
    source: str = "ios_corelocation"


class UploadTripPointsRequest(APIModel):
    batch_id: str | None = None
    points: list[TripPointIn]


class UploadTripPointsResponse(APIModel):
    accepted_count: int
    rejected_count: int = 0
    trip_status: str | None = None


class EndTripRequest(APIModel):
    ended_at: datetime | None = None
    device_distance_meters: float | None = None
    end_location: Coordinates | None = None


class EndTripResponse(APIModel):
    trip_id: str
    status: str
    ended_at: datetime
    summary: dict[str, Any] | None = None


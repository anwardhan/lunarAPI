from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class PortalLoginRequest(APIModel):
    password: str


class PortalSessionResponse(APIModel):
    authenticated: bool = True


class PortalDriverSummary(APIModel):
    driver_id: str
    display_name: str | None = None
    email: str | None = None


class PortalTripSummary(APIModel):
    trip_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    point_count: int
    total_distance_meters: float | None = None
    device_distance_meters: float | None = None
    sticker_submission_count: int = 0
    odometer_submission_count: int = 0
    driver: PortalDriverSummary


class PortalTripPoint(APIModel):
    recorded_at: datetime
    latitude: float
    longitude: float
    horizontal_accuracy: float
    speed_mps: float | None = None
    course_degrees: float | None = None
    altitude_meters: float | None = None
    source: str


class PortalPhotoSummary(APIModel):
    submission_id: str
    kind: str
    review_status: str
    submitted_at: datetime
    taken_at: datetime
    storage_key: str
    file_name: str | None = None
    trip_id: str | None = None
    driver: PortalDriverSummary
    image_url: str | None = None


class PortalDashboardResponse(APIModel):
    trips: list[PortalTripSummary]
    recent_photos: list[PortalPhotoSummary]


class PortalTripDetailResponse(APIModel):
    trip: PortalTripSummary
    points: list[PortalTripPoint]
    photos: list[PortalPhotoSummary]

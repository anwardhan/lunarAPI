from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class SubmissionCreateRequest(APIModel):
    storage_key: str
    taken_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    trip_id: str | None = None


class SubmissionResponse(APIModel):
    id: str
    status: str
    storage_key: str
    created_at: datetime


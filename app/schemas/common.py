from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


def serialize_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


class APIModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={datetime: serialize_datetime},
    )


class ErrorResponse(APIModel):
    detail: str


class Coordinates(APIModel):
    latitude: float
    longitude: float
    horizontal_accuracy: float | None = None


class DeviceInfo(APIModel):
    platform: str = "ios"
    app_version: str | None = None
    os_version: str | None = None


class CreatedRecordResponse(APIModel):
    id: str
    status: str
    created_at: datetime

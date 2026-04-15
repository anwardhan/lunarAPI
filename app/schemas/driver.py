from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class DriverResponse(APIModel):
    driver_id: str
    email: str | None = None
    display_name: str | None = None
    created_at: datetime


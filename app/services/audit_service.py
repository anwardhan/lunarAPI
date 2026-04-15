from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.models.audit_event import AuditEvent


async def record_audit_event(
    session: AsyncSession,
    event_type: str,
    driver_id: str | None = None,
    trip_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(
            event_type=event_type,
            driver_id=driver_id,
            trip_id=trip_id,
            metadata_json=metadata,
            created_at=utc_now(),
        )
    )


from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import public_id
from app.core.time import utc_now
from app.models.driver import Driver
from app.models.submission import OdometerSubmission, StickerSubmission
from app.models.trip import Trip
from app.schemas.submissions import SubmissionCreateRequest, SubmissionResponse
from app.services.audit_service import record_audit_event
from app.services.media_service import MediaService


class SubmissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.media_service = MediaService(session)

    async def create_sticker_submission(
        self,
        driver: Driver,
        request: SubmissionCreateRequest,
    ) -> SubmissionResponse:
        media = await self.media_service.ensure_media_for_submission(
            driver=driver,
            storage_key=request.storage_key,
            kind="sticker_photo",
        )
        trip_fk = await self._resolve_trip_fk(driver, request.trip_id)
        now = utc_now()
        submission = StickerSubmission(
            submission_id=public_id("stkr"),
            driver_fk=driver.id,
            media_object_fk=media.id,
            trip_fk=trip_fk,
            submitted_at=now,
            taken_at=request.taken_at,
            gps_lat=request.latitude,
            gps_lng=request.longitude,
            review_status="pending_review",
            created_at=now,
        )
        self.session.add(submission)
        await record_audit_event(
            self.session,
            event_type="submission.sticker_created",
            driver_id=driver.driver_id,
            trip_id=request.trip_id,
            metadata={"storage_key": request.storage_key},
        )
        await self.session.commit()
        await self.session.refresh(submission)
        return SubmissionResponse(
            id=submission.submission_id,
            status=submission.review_status,
            storage_key=request.storage_key,
            created_at=submission.created_at,
        )

    async def create_odometer_submission(
        self,
        driver: Driver,
        request: SubmissionCreateRequest,
    ) -> SubmissionResponse:
        media = await self.media_service.ensure_media_for_submission(
            driver=driver,
            storage_key=request.storage_key,
            kind="odometer_photo",
        )
        trip_fk = await self._resolve_trip_fk(driver, request.trip_id)
        now = utc_now()
        submission = OdometerSubmission(
            submission_id=public_id("odo"),
            driver_fk=driver.id,
            media_object_fk=media.id,
            trip_fk=trip_fk,
            submitted_at=now,
            taken_at=request.taken_at,
            gps_lat=request.latitude,
            gps_lng=request.longitude,
            review_status="pending_review",
            created_at=now,
        )
        self.session.add(submission)
        await record_audit_event(
            self.session,
            event_type="submission.odometer_created",
            driver_id=driver.driver_id,
            trip_id=request.trip_id,
            metadata={"storage_key": request.storage_key},
        )
        await self.session.commit()
        await self.session.refresh(submission)
        return SubmissionResponse(
            id=submission.submission_id,
            status=submission.review_status,
            storage_key=request.storage_key,
            created_at=submission.created_at,
        )

    async def _resolve_trip_fk(self, driver: Driver, trip_id: str | None) -> str | None:
        if trip_id is None:
            return None
        trip = (
            await self.session.execute(
                select(Trip).where(Trip.trip_id == trip_id, Trip.driver_fk == driver.id)
            )
        ).scalar_one_or_none()
        if trip is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
        return trip.id


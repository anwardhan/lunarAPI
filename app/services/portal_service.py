from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import StorageService
from app.models.driver import Driver
from app.models.media import MediaObject
from app.models.submission import OdometerSubmission, StickerSubmission
from app.models.trip import Trip, TripPoint
from app.schemas.portal import (
    PortalDashboardResponse,
    PortalDriverSummary,
    PortalPhotoSummary,
    PortalTripDetailResponse,
    PortalTripPoint,
    PortalTripSummary,
)


class PortalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = StorageService()

    async def get_dashboard(self, *, trip_limit: int = 25, photo_limit: int = 18) -> PortalDashboardResponse:
        trip_rows = (
            await self.session.execute(
                select(Trip, Driver)
                .join(Driver, Driver.id == Trip.driver_fk)
                .order_by(Trip.started_at.desc(), Trip.created_at.desc())
                .limit(trip_limit)
            )
        ).all()
        trip_counts = await self._load_submission_counts([trip.id for trip, _driver in trip_rows])
        trips = [
            self._serialize_trip(
                trip,
                driver,
                sticker_count=trip_counts["sticker"].get(trip.id, 0),
                odometer_count=trip_counts["odometer"].get(trip.id, 0),
            )
            for trip, driver in trip_rows
        ]
        recent_photos = await self._load_recent_photos(limit=photo_limit)
        return PortalDashboardResponse(trips=trips, recent_photos=recent_photos)

    async def get_trip_detail(self, trip_id: str) -> PortalTripDetailResponse:
        trip_row = (
            await self.session.execute(
                select(Trip, Driver)
                .join(Driver, Driver.id == Trip.driver_fk)
                .where(Trip.trip_id == trip_id)
            )
        ).first()
        if trip_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        trip, driver = trip_row
        counts = await self._load_submission_counts([trip.id])
        points = (
            await self.session.execute(
                select(TripPoint)
                .where(TripPoint.trip_fk == trip.id)
                .order_by(TripPoint.recorded_at.asc(), TripPoint.id.asc())
            )
        ).scalars().all()

        return PortalTripDetailResponse(
            trip=self._serialize_trip(
                trip,
                driver,
                sticker_count=counts["sticker"].get(trip.id, 0),
                odometer_count=counts["odometer"].get(trip.id, 0),
            ),
            points=[
                PortalTripPoint(
                    recorded_at=point.recorded_at,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    horizontal_accuracy=point.horizontal_accuracy,
                    speed_mps=point.speed_mps,
                    course_degrees=point.course_degrees,
                    altitude_meters=point.altitude_meters,
                    source=point.source,
                )
                for point in points
            ],
            photos=await self._load_trip_photos(trip.id),
        )

    async def get_media_file(self, kind: str, submission_id: str) -> tuple[Path, str]:
        if kind == "sticker":
            media = await self._media_for_sticker_submission(submission_id)
        elif kind == "odometer":
            media = await self._media_for_odometer_submission(submission_id)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

        path = self.storage.local_path_for_key(media.storage_key)
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file is not available on this server",
            )
        return path, media.content_type

    async def _load_submission_counts(self, trip_ids: list[str]) -> dict[str, dict[str, int]]:
        if not trip_ids:
            return {"sticker": {}, "odometer": {}}

        sticker_rows = (
            await self.session.execute(
                select(StickerSubmission.trip_fk, func.count(StickerSubmission.id))
                .where(StickerSubmission.trip_fk.in_(trip_ids))
                .group_by(StickerSubmission.trip_fk)
            )
        ).all()
        odometer_rows = (
            await self.session.execute(
                select(OdometerSubmission.trip_fk, func.count(OdometerSubmission.id))
                .where(OdometerSubmission.trip_fk.in_(trip_ids))
                .group_by(OdometerSubmission.trip_fk)
            )
        ).all()
        return {
            "sticker": {trip_fk: count for trip_fk, count in sticker_rows if trip_fk is not None},
            "odometer": {trip_fk: count for trip_fk, count in odometer_rows if trip_fk is not None},
        }

    async def _load_recent_photos(self, *, limit: int) -> list[PortalPhotoSummary]:
        photos = [
            *(
                await self._load_sticker_photos(
                    select(StickerSubmission, MediaObject, Driver, Trip.trip_id)
                    .join(MediaObject, MediaObject.id == StickerSubmission.media_object_fk)
                    .join(Driver, Driver.id == StickerSubmission.driver_fk)
                    .outerjoin(Trip, Trip.id == StickerSubmission.trip_fk)
                    .order_by(StickerSubmission.submitted_at.desc())
                    .limit(limit)
                )
            ),
            *(
                await self._load_odometer_photos(
                    select(OdometerSubmission, MediaObject, Driver, Trip.trip_id)
                    .join(MediaObject, MediaObject.id == OdometerSubmission.media_object_fk)
                    .join(Driver, Driver.id == OdometerSubmission.driver_fk)
                    .outerjoin(Trip, Trip.id == OdometerSubmission.trip_fk)
                    .order_by(OdometerSubmission.submitted_at.desc())
                    .limit(limit)
                )
            ),
        ]
        photos.sort(key=lambda photo: photo.submitted_at, reverse=True)
        return photos[:limit]

    async def _load_trip_photos(self, trip_fk: str) -> list[PortalPhotoSummary]:
        photos = [
            *(
                await self._load_sticker_photos(
                    select(StickerSubmission, MediaObject, Driver, Trip.trip_id)
                    .join(MediaObject, MediaObject.id == StickerSubmission.media_object_fk)
                    .join(Driver, Driver.id == StickerSubmission.driver_fk)
                    .outerjoin(Trip, Trip.id == StickerSubmission.trip_fk)
                    .where(StickerSubmission.trip_fk == trip_fk)
                    .order_by(StickerSubmission.submitted_at.desc())
                )
            ),
            *(
                await self._load_odometer_photos(
                    select(OdometerSubmission, MediaObject, Driver, Trip.trip_id)
                    .join(MediaObject, MediaObject.id == OdometerSubmission.media_object_fk)
                    .join(Driver, Driver.id == OdometerSubmission.driver_fk)
                    .outerjoin(Trip, Trip.id == OdometerSubmission.trip_fk)
                    .where(OdometerSubmission.trip_fk == trip_fk)
                    .order_by(OdometerSubmission.submitted_at.desc())
                )
            ),
        ]
        photos.sort(key=lambda photo: photo.submitted_at, reverse=True)
        return photos

    async def _load_sticker_photos(self, statement) -> list[PortalPhotoSummary]:
        rows = (await self.session.execute(statement)).all()
        return [
            self._serialize_photo(
                kind="sticker",
                submission_id=submission.submission_id,
                review_status=submission.review_status,
                submitted_at=submission.submitted_at,
                taken_at=submission.taken_at,
                trip_id=trip_id,
                driver=driver,
                media=media,
            )
            for submission, media, driver, trip_id in rows
        ]

    async def _load_odometer_photos(self, statement) -> list[PortalPhotoSummary]:
        rows = (await self.session.execute(statement)).all()
        return [
            self._serialize_photo(
                kind="odometer",
                submission_id=submission.submission_id,
                review_status=submission.review_status,
                submitted_at=submission.submitted_at,
                taken_at=submission.taken_at,
                trip_id=trip_id,
                driver=driver,
                media=media,
            )
            for submission, media, driver, trip_id in rows
        ]

    async def _media_for_sticker_submission(self, submission_id: str) -> MediaObject:
        row = (
            await self.session.execute(
                select(MediaObject)
                .join(StickerSubmission, StickerSubmission.media_object_fk == MediaObject.id)
                .where(StickerSubmission.submission_id == submission_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
        return row

    async def _media_for_odometer_submission(self, submission_id: str) -> MediaObject:
        row = (
            await self.session.execute(
                select(MediaObject)
                .join(OdometerSubmission, OdometerSubmission.media_object_fk == MediaObject.id)
                .where(OdometerSubmission.submission_id == submission_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
        return row

    def _serialize_trip(
        self,
        trip: Trip,
        driver: Driver,
        *,
        sticker_count: int,
        odometer_count: int,
    ) -> PortalTripSummary:
        return PortalTripSummary(
            trip_id=trip.trip_id,
            status=trip.status,
            started_at=trip.started_at,
            ended_at=trip.ended_at,
            point_count=trip.point_count,
            total_distance_meters=trip.total_distance_meters,
            device_distance_meters=trip.device_distance_meters,
            sticker_submission_count=sticker_count,
            odometer_submission_count=odometer_count,
            driver=self._serialize_driver(driver),
        )

    def _serialize_photo(
        self,
        *,
        kind: str,
        submission_id: str,
        review_status: str,
        submitted_at,
        taken_at,
        trip_id: str | None,
        driver: Driver,
        media: MediaObject,
    ) -> PortalPhotoSummary:
        path = self.storage.local_path_for_key(media.storage_key)
        return PortalPhotoSummary(
            submission_id=submission_id,
            kind=kind,
            review_status=review_status,
            submitted_at=submitted_at,
            taken_at=taken_at,
            storage_key=media.storage_key,
            file_name=media.original_file_name,
            trip_id=trip_id,
            driver=self._serialize_driver(driver),
            image_url=f"/portal/media/{kind}/{submission_id}" if path.is_file() else None,
        )

    @staticmethod
    def _serialize_driver(driver: Driver) -> PortalDriverSummary:
        return PortalDriverSummary(
            driver_id=driver.driver_id,
            display_name=driver.full_name,
            email=driver.primary_email,
        )

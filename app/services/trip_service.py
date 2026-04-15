from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import public_id
from app.core.time import utc_now
from app.models.driver import Driver
from app.models.trip import Trip, TripPoint, TripPointBatch
from app.schemas.trip import (
    EndTripRequest,
    EndTripResponse,
    StartTripRequest,
    TripResponse,
    UploadTripPointsRequest,
    UploadTripPointsResponse,
)
from app.services.audit_service import record_audit_event


class TripService:
    ACCEPTING_POINT_STATUSES = {"active", "ending", "upload_delayed"}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_trip(self, driver: Driver, request: StartTripRequest) -> TripResponse:
        if request.client_trip_id:
            existing = (
                await self.session.execute(
                    select(Trip).where(
                        Trip.driver_fk == driver.id,
                        Trip.client_trip_id == request.client_trip_id,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                return self.to_response(existing, driver)

        now = utc_now()
        started_at = request.started_at or now
        device = request.device
        start_location = request.start_location
        trip = Trip(
            trip_id=public_id("trip"),
            driver_fk=driver.id,
            client_trip_id=request.client_trip_id,
            status="active",
            started_at=started_at,
            start_lat=start_location.latitude if start_location else None,
            start_lng=start_location.longitude if start_location else None,
            device_platform=device.platform if device else "ios",
            app_version=device.app_version if device else None,
            os_version=device.os_version if device else None,
            point_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(trip)
        await record_audit_event(
            self.session,
            event_type="trip.start",
            driver_id=driver.driver_id,
            trip_id=trip.trip_id,
        )
        await self.session.commit()
        await self.session.refresh(trip)
        return self.to_response(trip, driver)

    async def ingest_points(
        self,
        driver: Driver,
        trip_id: str,
        request: UploadTripPointsRequest,
    ) -> UploadTripPointsResponse:
        trip = await self._get_owned_trip(driver, trip_id)
        if trip.status not in self.ACCEPTING_POINT_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trip is not active")

        if request.batch_id:
            existing_batch = (
                await self.session.execute(
                    select(TripPointBatch).where(
                        TripPointBatch.trip_fk == trip.id,
                        TripPointBatch.batch_id == request.batch_id,
                    )
                )
            ).scalar_one_or_none()
            if existing_batch is not None:
                return UploadTripPointsResponse(
                    accepted_count=existing_batch.accepted_count,
                    rejected_count=0,
                    trip_status=trip.status,
                )

        now = utc_now()
        accepted_count = 0
        rejected_count = 0
        for point in request.points:
            existing_point = (
                await self.session.execute(
                    select(TripPoint.id).where(
                        TripPoint.trip_fk == trip.id,
                        TripPoint.recorded_at == point.timestamp,
                        TripPoint.latitude == point.latitude,
                        TripPoint.longitude == point.longitude,
                    )
                )
            ).scalar_one_or_none()
            if existing_point is not None:
                continue
            self.session.add(
                TripPoint(
                    trip_fk=trip.id,
                    recorded_at=point.timestamp,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    horizontal_accuracy=point.horizontal_accuracy,
                    vertical_accuracy=point.vertical_accuracy,
                    speed_mps=point.speed_mps,
                    course_degrees=point.course_degrees,
                    altitude_meters=point.altitude_meters,
                    source=point.source,
                    created_at=now,
                )
            )
            accepted_count += 1

        if request.batch_id:
            self.session.add(
                TripPointBatch(
                    trip_fk=trip.id,
                    batch_id=request.batch_id,
                    accepted_count=accepted_count,
                    created_at=now,
                )
            )

        trip.point_count += accepted_count
        trip.updated_at = now
        await record_audit_event(
            self.session,
            event_type="trip.points_ingested",
            driver_id=driver.driver_id,
            trip_id=trip.trip_id,
            metadata={"accepted_count": accepted_count, "batch_id": request.batch_id},
        )
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate batch")

        return UploadTripPointsResponse(
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            trip_status=trip.status,
        )

    async def end_trip(
        self,
        driver: Driver,
        trip_id: str,
        request: EndTripRequest,
    ) -> EndTripResponse:
        trip = await self._get_owned_trip(driver, trip_id)
        now = utc_now()
        if trip.status == "completed" and trip.ended_at is not None:
            return self.to_end_response(trip)

        ended_at = request.ended_at or now
        trip.status = "completed"
        trip.ended_at = ended_at
        trip.device_distance_meters = request.device_distance_meters
        trip.total_distance_meters = request.device_distance_meters
        if request.end_location:
            trip.end_lat = request.end_location.latitude
            trip.end_lng = request.end_location.longitude
        trip.updated_at = now
        await record_audit_event(
            self.session,
            event_type="trip.end",
            driver_id=driver.driver_id,
            trip_id=trip.trip_id,
        )
        await self.session.commit()
        await self.session.refresh(trip)
        return self.to_end_response(trip)

    async def _get_owned_trip(self, driver: Driver, trip_id: str) -> Trip:
        trip = (
            await self.session.execute(
                select(Trip).where(Trip.trip_id == trip_id, Trip.driver_fk == driver.id)
            )
        ).scalar_one_or_none()
        if trip is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
        return trip

    @staticmethod
    def to_response(trip: Trip, driver: Driver) -> TripResponse:
        return TripResponse(
            trip_id=trip.trip_id,
            driver_id=driver.driver_id,
            started_at=trip.started_at,
            ended_at=trip.ended_at,
            status=trip.status,
        )

    @staticmethod
    def to_end_response(trip: Trip) -> EndTripResponse:
        ended_at = trip.ended_at or utc_now()
        duration_seconds = max(0, int((ended_at - trip.started_at).total_seconds()))
        return EndTripResponse(
            trip_id=trip.trip_id,
            status=trip.status,
            ended_at=ended_at,
            summary={
                "point_count": trip.point_count,
                "distance_meters": trip.total_distance_meters,
                "duration_seconds": duration_seconds,
            },
        )


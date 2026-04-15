from __future__ import annotations

from fastapi import APIRouter

from app.api.deps.auth import CurrentDriver, DbSession
from app.schemas.trip import (
    EndTripRequest,
    EndTripResponse,
    StartTripRequest,
    TripResponse,
    UploadTripPointsRequest,
    UploadTripPointsResponse,
)
from app.services.trip_service import TripService

router = APIRouter(tags=["trips"])


@router.post("/trips/start", response_model=TripResponse)
async def start_trip(
    request: StartTripRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> TripResponse:
    return await TripService(session).start_trip(driver, request)


@router.post("/trips/{trip_id}/points", response_model=UploadTripPointsResponse)
async def upload_trip_points(
    trip_id: str,
    request: UploadTripPointsRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> UploadTripPointsResponse:
    return await TripService(session).ingest_points(driver, trip_id, request)


@router.post("/trips/{trip_id}/end", response_model=EndTripResponse)
async def end_trip(
    trip_id: str,
    request: EndTripRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> EndTripResponse:
    return await TripService(session).end_trip(driver, trip_id, request)


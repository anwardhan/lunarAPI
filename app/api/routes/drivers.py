from __future__ import annotations

from fastapi import APIRouter

from app.api.deps.auth import CurrentDriver
from app.schemas.driver import DriverResponse
from app.services.driver_service import DriverService

router = APIRouter(tags=["drivers"])


@router.get("/me", response_model=DriverResponse)
async def get_me(driver: CurrentDriver) -> DriverResponse:
    return DriverService.to_response(driver)


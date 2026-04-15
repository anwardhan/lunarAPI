from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.schemas.driver import DriverResponse
from app.services.auth_service import AuthService


class DriverService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_driver_id(self, driver_id: str) -> Driver:
        driver = (
            await self.session.execute(select(Driver).where(Driver.driver_id == driver_id))
        ).scalar_one_or_none()
        if driver is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Driver not found")
        return driver

    @staticmethod
    def to_response(driver: Driver) -> DriverResponse:
        return AuthService.to_driver_response(driver)


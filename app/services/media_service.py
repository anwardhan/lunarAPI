from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.ids import public_id
from app.core.storage import StorageService
from app.core.time import utc_now
from app.models.driver import Driver
from app.models.media import MediaObject
from app.schemas.media import CreateUploadURLRequest, UploadURLResponse
from app.services.audit_service import record_audit_event


class MediaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.storage = StorageService(self.settings)

    async def create_upload_url(
        self,
        driver: Driver,
        request: CreateUploadURLRequest,
    ) -> UploadURLResponse:
        kind = request.normalized_kind
        if kind not in {"sticker_photo", "odometer_photo"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid media kind")

        now = utc_now()
        object_key = self.storage.build_object_key(driver.driver_id, kind, request.file_name)
        self.session.add(
            MediaObject(
                media_id=public_id("media"),
                driver_fk=driver.id,
                kind=kind,
                storage_key=object_key,
                bucket_name=self.settings.storage_bucket,
                content_type=request.content_type,
                original_file_name=request.file_name,
                file_size_bytes=request.file_size_bytes,
                processing_status="pending_upload",
                created_at=now,
            )
        )
        await record_audit_event(
            self.session,
            event_type="media.upload_url_created",
            driver_id=driver.driver_id,
            metadata={"kind": kind, "storage_key": object_key},
        )
        await self.session.commit()
        return UploadURLResponse(
            upload_url=self.storage.create_upload_target(object_key),
            storage_key=object_key,
            object_key=object_key,
            public_url=None,
            expires_in_seconds=900,
        )

    async def mark_dev_upload_complete(self, object_key: str, body: bytes) -> None:
        path = self.storage.local_path_for_key(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

        media = (
            await self.session.execute(select(MediaObject).where(MediaObject.storage_key == object_key))
        ).scalar_one_or_none()
        if media is not None:
            media.processing_status = "uploaded"
            media.verified_uploaded_at = utc_now()
            await self.session.commit()

    async def get_media_for_driver(self, driver: Driver, storage_key: str) -> MediaObject | None:
        media = (
            await self.session.execute(select(MediaObject).where(MediaObject.storage_key == storage_key))
        ).scalar_one_or_none()
        if media is not None and media.driver_fk != driver.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Media belongs to another driver")
        return media

    async def ensure_media_for_submission(
        self,
        driver: Driver,
        storage_key: str,
        kind: str,
    ) -> MediaObject:
        media = await self.get_media_for_driver(driver, storage_key)
        if media is not None:
            return media

        now = utc_now()
        media = MediaObject(
            media_id=public_id("media"),
            driver_fk=driver.id,
            kind=kind,
            storage_key=storage_key,
            bucket_name=self.settings.storage_bucket,
            content_type="image/jpeg",
            original_file_name=Path(storage_key).name,
            processing_status="metadata_received",
            created_at=now,
        )
        self.session.add(media)
        await self.session.flush()
        return media


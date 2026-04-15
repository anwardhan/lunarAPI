from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.api.deps.auth import CurrentDriver, DbSession
from app.schemas.media import CreateUploadURLRequest, UploadURLResponse
from app.services.media_service import MediaService

router = APIRouter(tags=["media"])


@router.post("/media/upload-url", response_model=UploadURLResponse)
async def create_upload_url(
    request: CreateUploadURLRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> UploadURLResponse:
    return await MediaService(session).create_upload_url(driver, request)


@router.put("/media/dev-upload/{object_key:path}", include_in_schema=False)
async def dev_upload_object(object_key: str, request: Request, session: DbSession) -> Response:
    body = await request.body()
    await MediaService(session).mark_dev_upload_complete(object_key, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


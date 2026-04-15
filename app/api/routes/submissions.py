from __future__ import annotations

from fastapi import APIRouter

from app.api.deps.auth import CurrentDriver, DbSession
from app.schemas.submissions import SubmissionCreateRequest, SubmissionResponse
from app.services.submission_service import SubmissionService

router = APIRouter(tags=["submissions"])


@router.post("/submissions/sticker", response_model=SubmissionResponse)
@router.post("/sticker-verifications", response_model=SubmissionResponse)
async def create_sticker_submission(
    request: SubmissionCreateRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> SubmissionResponse:
    return await SubmissionService(session).create_sticker_submission(driver, request)


@router.post("/submissions/odometer", response_model=SubmissionResponse)
@router.post("/odometer-submissions", response_model=SubmissionResponse)
async def create_odometer_submission(
    request: SubmissionCreateRequest,
    driver: CurrentDriver,
    session: DbSession,
) -> SubmissionResponse:
    return await SubmissionService(session).create_odometer_submission(driver, request)


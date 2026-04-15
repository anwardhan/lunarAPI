from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class CreateUploadURLRequest(APIModel):
    kind: str | None = None
    media_type: str | None = None
    content_type: str = "image/jpeg"
    file_name: str | None = None
    file_size_bytes: int | None = Field(default=None, ge=0)

    @property
    def normalized_kind(self) -> str:
        return self.kind or self.media_type or "sticker_photo"


class UploadURLResponse(APIModel):
    upload_url: str
    storage_key: str
    object_key: str
    public_url: str | None = None
    expires_in_seconds: int = 900


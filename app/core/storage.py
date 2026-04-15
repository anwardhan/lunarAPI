from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.ids import public_id
from app.core.time import utc_now


class StorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def build_object_key(self, driver_id: str, kind: str, file_name: str | None) -> str:
        suffix = file_name.rsplit(".", 1)[-1].lower() if file_name and "." in file_name else "jpg"
        today = utc_now()
        return (
            f"driver_uploads/{driver_id}/{kind}/"
            f"{today:%Y/%m/%d}/{public_id('media')}.{suffix}"
        )

    def create_upload_target(self, object_key: str) -> str:
        # Local development placeholder for object storage presigning. It intentionally only
        # exists as an upload target returned after authenticated API authorization.
        return f"{self.settings.api_base_url.rstrip('/')}/v1/media/dev-upload/{object_key}"

    def local_path_for_key(self, object_key: str) -> Path:
        root = Path(self.settings.local_upload_root)
        safe_parts = [part for part in object_key.split("/") if part not in {"", ".", ".."}]
        return root.joinpath(*safe_parts)


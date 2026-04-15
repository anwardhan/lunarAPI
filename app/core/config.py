from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+asyncpg://lunar:lunar@localhost:5432/lunar_car"
    jwt_secret: str = Field(default="dev-only-change-me-at-least-32-bytes")
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 30
    auth_provider_verification: str = "development"
    local_upload_root: Path = Path("./local_uploads")
    storage_bucket: str = "lunar-car-local"


@lru_cache
def get_settings() -> Settings:
    return Settings()

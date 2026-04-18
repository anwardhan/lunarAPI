from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(value: str) -> str:
    database_url = value.strip().strip("\"'")
    if not database_url:
        raise ValueError("DATABASE_URL is empty.")
    if database_url.startswith("${") or database_url.startswith("$("):
        raise ValueError(
            "DATABASE_URL is unresolved. In DigitalOcean App Platform, bind it to the "
            "database component value such as ${postgres-db.DATABASE_URL}."
        )

    replacements = {
        "postgres://": "postgresql+asyncpg://",
        "postgresql://": "postgresql+asyncpg://",
        "postgresql+psycopg://": "postgresql+asyncpg://",
        "postgresql+psycopg2://": "postgresql+asyncpg://",
    }
    for prefix, replacement in replacements.items():
        if database_url.startswith(prefix):
            return replacement + database_url[len(prefix):]
    return database_url


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

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return normalize_database_url(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()

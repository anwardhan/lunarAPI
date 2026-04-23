from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
import ssl

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


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


def build_database_engine_config(value: str) -> tuple[str, dict[str, Any]]:
    database_url = normalize_database_url(value)
    connect_args: dict[str, Any] = {}
    url = make_url(database_url)

    if url.drivername != "postgresql+asyncpg":
        return database_url, connect_args

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    sslrootcert = query.pop("sslrootcert", None)
    sslcert = query.pop("sslcert", None)
    sslkey = query.pop("sslkey", None)
    sslcrl = query.pop("sslcrl", None)
    sslpassword = query.pop("sslpassword", None)

    if any(value is not None for value in (sslmode, sslrootcert, sslcert, sslkey, sslcrl)):
        if any(value is not None for value in (sslrootcert, sslcert, sslkey, sslcrl)):
            ssl_context = ssl.create_default_context(cafile=sslrootcert)
            if sslmode == "require":
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            elif sslmode == "verify-ca":
                ssl_context.check_hostname = False
            elif sslmode == "disable":
                connect_args["ssl"] = "disable"
                ssl_context = None
            if ssl_context is not None:
                if sslcert or sslkey:
                    ssl_context.load_cert_chain(sslcert, keyfile=sslkey, password=sslpassword)
                if sslcrl:
                    ssl_context.verify_flags |= ssl.VERIFY_CRL_CHECK_LEAF
                connect_args["ssl"] = ssl_context
        elif sslmode is not None:
            connect_args["ssl"] = sslmode

    sanitized_url = url.set(query=query).render_as_string(hide_password=False)
    return sanitized_url, connect_args


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

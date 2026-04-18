from __future__ import annotations

import pytest

from app.core.config import normalize_database_url


def test_normalize_database_url_accepts_plain_postgresql_url() -> None:
    assert normalize_database_url("postgresql://user:pass@db.example.com:25060/lunar") == (
        "postgresql+asyncpg://user:pass@db.example.com:25060/lunar"
    )


def test_normalize_database_url_accepts_quoted_postgres_url() -> None:
    assert normalize_database_url("'postgres://user:pass@db.example.com:25060/lunar'") == (
        "postgresql+asyncpg://user:pass@db.example.com:25060/lunar"
    )


def test_normalize_database_url_preserves_sqlite() -> None:
    assert normalize_database_url("sqlite+aiosqlite:///./lunar_car_dev.db") == (
        "sqlite+aiosqlite:///./lunar_car_dev.db"
    )


def test_normalize_database_url_rejects_unresolved_placeholder() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL is unresolved"):
        normalize_database_url("${postgres-db.DATABASE_URL}")

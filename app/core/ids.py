from __future__ import annotations

import secrets
import uuid


def uuid_str() -> str:
    return str(uuid.uuid4())


def public_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"


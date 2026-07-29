from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Depends(_api_key_header),
) -> str:
    """Validate X-API-Key header against settings.api_key.

    Returns the validated key on success, raises 401 on failure.
    When settings.api_key is empty/None, auth is skipped (dev mode).
    """
    if not settings.api_key:
        return ""

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "APIKey"},
        )

    if not hmac.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return api_key

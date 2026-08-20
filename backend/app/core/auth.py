from __future__ import annotations

import hmac
import logging
import os

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core.config import settings

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Detect production mode: any explicit ENVIRONMENT=production env var,
# or absence of DEBUG flag combined with a non-empty API key requirement.
_ENV = os.getenv("ENVIRONMENT", "development").lower()
_IS_PRODUCTION = _ENV in ("production", "prod")


async def require_api_key(
    api_key: str | None = Depends(_api_key_header),
) -> str:
    """Validate X-API-Key header against settings.api_key.

    Returns the validated key on success, raises 401/403 on failure.

    Behaviour by environment:
    - production: API key is REQUIRED; startup will already have failed-fast
      if it was missing, but we double-check here for defence-in-depth.
    - development: if api_key is empty we skip auth and log a warning once.
    """
    if not settings.api_key:
        if _IS_PRODUCTION:
            # Should never reach here because startup check catches it, but
            # be defensive.
            raise HTTPException(
                status_code=503,
                detail="Server misconfiguration: API_KEY must be set in production.",
            )
        # Dev mode – warn once and allow through
        logger.warning(
            "API_KEY is not set — authentication is DISABLED. "
            "Set API_KEY in your .env before deploying to production."
        )
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

"""Optional API-key authentication for the QR Code API.

Authentication is enabled when the ``QR_CODE_API_KEYS`` environment variable is set
to a non-empty, comma-separated list of valid keys. When unset or empty,
authentication is disabled (no-op) so the service remains zero-config for
local development and existing deployments.

Keys are transported as Bearer tokens in the ``Authorization`` header:

    Authorization: Bearer <key>

The Swagger UI (``/v{N}/docs``) automatically renders an "Authorize" button
that accepts the token, courtesy of FastAPI's ``HTTPBearer`` security scheme.
"""

import hmac
import os
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

API_KEYS_ENV_VAR = "QR_CODE_API_KEYS"

_bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="API key")


def _load_keys() -> set[str]:
    raw = os.environ.get(API_KEYS_ENV_VAR, "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def auth_enabled() -> bool:
    """Whether API-key authentication is currently active."""
    return bool(_load_keys())


async def require_api_key(
    creds: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> str:
    """FastAPI dependency enforcing a valid API key when auth is enabled."""
    valid_keys = _load_keys()
    if not valid_keys:
        # Auth disabled: accept anonymous requests.
        return ""

    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": 'Bearer realm="qr-code-api"'},
        )

    presented = creds.credentials
    # Constant-time comparison against every configured key to mitigate timing attacks.
    if not any(hmac.compare_digest(presented, valid) for valid in valid_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
            headers={"WWW-Authenticate": 'Bearer realm="qr-code-api"'},
        )

    return presented

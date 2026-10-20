"""
Pydantic schemas for authentication.
"""

from pydantic import BaseModel


class TokenPair(BaseModel):
    """Access + refresh token pair returned after login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Optional body for /auth/refresh (the cookie is used as a fallback)."""

    refresh_token: str | None = None

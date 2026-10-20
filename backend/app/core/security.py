"""
Security utilities for OpenEdu Git.

This module is the single source of truth for authentication: password
hashing, token creation/decoding and the ``get_current_user`` dependency.
"""

import logging
import secrets
import warnings
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User

logger = logging.getLogger(__name__)

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def _resolve_secret_key() -> str:
    """Return the configured secret, or an ephemeral one for local development."""
    if settings.SECRET_KEY:
        return settings.SECRET_KEY
    warnings.warn(
        "SECRET_KEY is not set - generating an ephemeral key. "
        "All sessions become invalid on restart. Set SECRET_KEY before deploying.",
        RuntimeWarning,
        stacklevel=2,
    )
    return secrets.token_urlsafe(48)


_SECRET_KEY = _resolve_secret_key()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.PASSWORD_HASH_ROUNDS,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash for a password."""
    return pwd_context.hash(password)


# --------------------------------------------------------------------------- #
# Tokens
# --------------------------------------------------------------------------- #
def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    to_encode.update(
        {
            "exp": now + expires_delta,
            "iat": now,
            "type": token_type,
        }
    )
    return jwt.encode(to_encode, _SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token for the given subject (user id)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token({"sub": subject}, TOKEN_TYPE_ACCESS, delta)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived refresh token for the given subject (user id).

    Refresh tokens carry a ``jti`` so they can be revoked individually
    (see :func:`revoke_refresh_token`).
    """
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token({"sub": subject, "jti": uuid4().hex}, TOKEN_TYPE_REFRESH, delta)


def decode_token(token: str, expected_type: str = TOKEN_TYPE_ACCESS) -> dict | None:
    """Decode a JWT and return its payload, or ``None`` when invalid/expired.

    ``expected_type`` prevents a refresh token from being replayed as an access
    token (and vice versa).
    """
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def revoke_refresh_token(db: Session, payload: dict) -> None:
    """Add a refresh token's ``jti`` to the denylist (idempotent)."""
    jti = payload.get("jti")
    exp = payload.get("exp")
    user_id = _user_id_from_payload(payload)
    if not jti or exp is None or user_id is None:
        return
    existing = db.query(RevokedToken).filter(RevokedToken.jti == str(jti)).first()
    if existing:
        return
    db.add(
        RevokedToken(
            jti=str(jti),
            user_id=user_id,
            expires_at=datetime.fromtimestamp(exp, tz=UTC),
        )
    )
    # Opportunistic cleanup: denylist entries past expiry can never match.
    db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.now(UTC)).delete()
    db.commit()


def is_refresh_token_revoked(db: Session, payload: dict) -> bool:
    """True when the token's ``jti`` is on the denylist."""
    jti = payload.get("jti")
    if not jti:
        # Tokens minted before revocation existed carry no jti; treat them as
        # valid so a deploy does not log everyone out.
        return False
    return db.query(RevokedToken.id).filter(RevokedToken.jti == str(jti)).first() is not None


def _user_id_from_payload(payload: dict) -> int | None:
    raw = payload.get("sub")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Dependencies
# --------------------------------------------------------------------------- #
def _extract_token(request: Request, header_token: str | None) -> str | None:
    """Prefer the Authorization header, fall back to the httpOnly cookie."""
    if header_token:
        return header_token
    cookie = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if cookie:
        return cookie.removeprefix("Bearer ").strip()
    return None


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the active user for the request, or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token = _extract_token(request, token)
    if not raw_token:
        raise credentials_exception

    payload = decode_token(raw_token)
    if not payload:
        raise credentials_exception

    user_id = _user_id_from_payload(payload)
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def get_optional_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user when credentials are present and valid."""
    try:
        return get_current_user(request=request, token=token, db=db)
    except HTTPException:
        return None


# --------------------------------------------------------------------------- #
# Cookies
# --------------------------------------------------------------------------- #
def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Store the tokens in httpOnly cookies."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove the authentication cookies."""
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")

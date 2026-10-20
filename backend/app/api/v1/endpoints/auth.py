"""
Authentication endpoints for OpenEdu Git API v1.
"""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ....core.config import settings
from ....core.email import send_verification_email
from ....core.security import (
    REFRESH_TOKEN_COOKIE,
    TOKEN_TYPE_REFRESH,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    is_refresh_token_revoked,
    revoke_refresh_token,
    set_auth_cookies,
)
from ....db.session import get_db
from ....models.user import User as UserModel
from ....models.verification_token import VerificationToken
from ....schemas.auth import RefreshRequest, TokenPair
from ....schemas.user import User, UserCreate
from ....services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(response: Response, user: UserModel) -> TokenPair:
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    set_auth_cookies(response, access_token, refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


def _create_verification_token(db: Session, user: UserModel) -> str:
    """Replace any outstanding token for the user and return the new one."""
    db.query(VerificationToken).filter(VerificationToken.user_id == user.id).delete()
    raw_token = secrets.token_urlsafe(32)
    db.add(
        VerificationToken(
            user_id=user.id,
            token=raw_token,
            purpose="email",
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS),
        )
    )
    db.commit()
    return raw_token


def _start_verification(db: Session, user: UserModel) -> None:
    """Create a verification token and email the link (best effort)."""
    raw_token = _create_verification_token(db, user)
    send_verification_email(user.email, raw_token)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new user and start a session."""
    if UserService.get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    requires_verification = settings.REQUIRE_EMAIL_VERIFICATION
    created_user = UserService.create_user(
        db,
        user=user,
        is_verified=not requires_verification,
    )
    if requires_verification:
        _start_verification(db, created_user)
    else:
        _issue_tokens(response, created_user)
    return created_user


class VerificationRequest(BaseModel):
    email: EmailStr


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Mark an email address as verified using the emailed token.

    Idempotent: a token that was already used reports success as long as the
    account is verified.
    """
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token",
    )
    stored = db.query(VerificationToken).filter(VerificationToken.token == token).first()
    if stored is None:
        raise invalid

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise invalid

    user = UserService.get_user_by_id(db, user_id=stored.user_id)
    if user is None:
        raise invalid

    # The token is left in place until it expires so re-clicking the link
    # (or refreshing the page) keeps working; it grants nothing extra.
    user.is_verified = 1
    db.commit()
    return {"message": "Email verified successfully", "email": user.email}


@router.post("/resend-verification")
def resend_verification(payload: VerificationRequest, db: Session = Depends(get_db)):
    """Send a fresh verification email for an unverified account."""
    user = UserService.get_user_by_email(db, email=payload.email)
    # Always answer 200 so this endpoint cannot be used to probe registrations.
    if user and not user.is_verified:
        _start_verification(db, user)
    return {"message": "If the account exists and is unverified, a verification email was sent."}


@router.post("/login", response_model=TokenPair)
def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with email + password and receive tokens (also set as cookies)."""
    user = UserService.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email address is not verified"
        )

    return _issue_tokens(response, user)


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    """Exchange a refresh token for a new token pair."""
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get(
        REFRESH_TOKEN_COOKIE
    )
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    token_payload = decode_token(raw_token, expected_type=TOKEN_TYPE_REFRESH)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if is_refresh_token_revoked(db, token_payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )

    try:
        user_id = int(token_payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from None

    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return _issue_tokens(response, user)


@router.post("/logout")
def logout_user(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    """Clear the session: revoke the refresh token and delete the cookies."""
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get(
        REFRESH_TOKEN_COOKIE
    )
    if raw_token:
        token_payload = decode_token(raw_token, expected_type=TOKEN_TYPE_REFRESH)
        if token_payload:
            revoke_refresh_token(db, token_payload)
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """Return the authenticated user."""
    return current_user

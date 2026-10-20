"""
Authentication endpoints for OpenEdu Git API v1.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ....core.config import settings
from ....core.security import (
    REFRESH_TOKEN_COOKIE,
    TOKEN_TYPE_REFRESH,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    set_auth_cookies,
)
from ....db.session import get_db
from ....models.user import User as UserModel
from ....schemas.auth import RefreshRequest, TokenPair
from ....schemas.user import User, UserCreate
from ....services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(response: Response, user: UserModel) -> TokenPair:
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    set_auth_cookies(response, access_token, refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new user and start a session."""
    if UserService.get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    created_user = UserService.create_user(
        db,
        user=user,
        is_verified=not settings.REQUIRE_EMAIL_VERIFICATION,
    )
    _issue_tokens(response, created_user)
    return created_user


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
def logout_user(response: Response):
    """Clear the authentication cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """Return the authenticated user."""
    return current_user

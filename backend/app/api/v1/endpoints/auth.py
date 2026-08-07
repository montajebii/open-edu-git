"""
Authentication endpoints for OpenEdu Git API v1.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from ...core.config import settings
from ...core.auth import (
    create_access_token,
    create_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user,
)
from ...db.session import get_db
from ...services.user import UserService
from ...schemas.user import UserCreate, User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    response: Response = None,
):
    """Register a new user."""
    db_user = UserService.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    created_user = UserService.create_user(db, user=user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(created_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(created_user.id)})
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return created_user


@router.post("/login")
def login_user(
    email: str,
    password: str,
    db: Session = Depends(get_db),
    response: Response = None,
):
    """Login user and set auth cookies."""
    user = UserService.authenticate_user(db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return {"message": "Login successful", "user_id": str(user.id)}


@router.post("/logout")
def logout_user(response: Response):
    """Logout user by clearing auth cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
def read_current_user(
    current_user: Annotated[UUID, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Get current user details."""
    user = UserService.get_user_by_id(db, user_id=current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
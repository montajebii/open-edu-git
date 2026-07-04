"""
Authentication routes for OpenEdu Git.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
import secrets

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.core.email import send_verification_email
from app.schemas.user import UserCreate, User
from app.schemas.verification_token import VerificationTokenCreate
from app.models.user import User as UserModel
from app.models.verification_token import VerificationToken
from app.db.session import get_db

router = APIRouter()


@router.post("/register", response_model=User)
def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if email already exists
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create user
    db_user = UserModel(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        title=user.title,
        bio=user.bio,
        is_verified=False  # Email verification required
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create verification token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    db_token = VerificationToken(
        user_id=db_user.id,
        token=token,
        purpose="email_verification",
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    # Send verification email in background
    background_tasks.add_task(send_verification_email, db_user.email, token)
    
    return db_user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify a user's email."""
    # Check token exists and is valid
    db_token = db.query(VerificationToken).filter(
        VerificationToken.token == token,
        VerificationToken.purpose == "email_verification",
        VerificationToken.expires_at > datetime.utcnow()
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Update user
    db_user = db.query(UserModel).filter(UserModel.id == db_token.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_user.is_verified = True
    db.delete(db_token)
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login a user and return JWT tokens."""
    # Check user exists
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active and verified
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_token(refresh_token: str):
    """Refresh an access token using a refresh token."""
    # Decode refresh token
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload["sub"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token."""
    from app.core.security import decode_token as security_decode_token
    return security_decode_token(token)
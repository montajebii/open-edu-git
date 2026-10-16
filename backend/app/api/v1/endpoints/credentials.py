"""
Credentials endpoints for OpenEdu Git API v1.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.user import User
from app.services.credentials import CredentialService

router = APIRouter()


@router.get("/users/{user_id}/credentials", response_model=User)
def get_user_credentials(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get user credentials and metrics."""
    user = CredentialService.update_user_credential(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/teachers/top", response_model=list[User])
def get_top_teachers(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get top teachers by credential score."""
    # Update credentials before returning results
    top_users = CredentialService.get_top_teachers(db, limit=limit)
    for user in top_users:
        CredentialService.update_user_credential(db, user.id)
    return CredentialService.get_top_teachers(db, limit=limit)


@router.get("/pamphlets/{pamphlet_id}/ip-distribution")
def get_pamphlet_ip_distribution(
    pamphlet_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get the intellectual property percentage distribution for a pamphlet.

    Returns a dict mapping contributor user IDs to their IP percentage.
    """
    from app.services.ip_calculation import IPCalculationService

    distribution = IPCalculationService.calculate_pamphlet_ip_distribution(db, pamphlet_id)
    if not distribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pamphlet not found",
        )

    # Convert UUID keys to strings for JSON serialization
    return {str(k): v for k, v in distribution.items()}


@router.get("/pamphlets/{pamphlet_id}/ip/{user_id}")
def get_user_ip_percentage(
    pamphlet_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Get the IP percentage for a specific user on a specific pamphlet."""
    from app.services.ip_calculation import IPCalculationService

    ip_percentage = IPCalculationService.get_user_ip_percentage(db, pamphlet_id, user_id)
    return {"pamphlet_id": str(pamphlet_id), "user_id": str(user_id), "ip_percentage": ip_percentage}

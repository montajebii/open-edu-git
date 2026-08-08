"""
Review endpoints for OpenEdu Git.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pamphlet import Pamphlet as PamphletModel
from app.models.review import Review as ReviewModel
from app.models.user import User as UserModel
from app.schemas.review import Review, ReviewCreate

router = APIRouter()


@router.post("/pamphlets/{pamphlet_id}/reviews", response_model=Review)
def create_review(
    pamphlet_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a review for a pamphlet."""
    # Check pamphlet exists
    db_pamphlet = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    if not db_pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")

    # Check if user already reviewed this pamphlet
    db_review = (
        db.query(ReviewModel)
        .filter(ReviewModel.pamphlet_id == pamphlet_id, ReviewModel.user_id == current_user.id)
        .first()
    )
    if db_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this pamphlet",
        )

    # Create review
    db_review = ReviewModel(
        pamphlet_id=pamphlet_id,
        user_id=current_user.id,
        rating=review.rating,
        comment=review.comment,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    return db_review


@router.get("/pamphlets/{pamphlet_id}/reviews", response_model=list[Review])
def get_pamphlet_reviews(pamphlet_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a pamphlet."""
    return db.query(ReviewModel).filter(ReviewModel.pamphlet_id == pamphlet_id).all()

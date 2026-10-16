"""
Teacher credential service for OpenEdu Git.

Calculates teacher credential scores based on:
- Number of pamphlets authored
- Average ratings received
- Number of forks received (popularity)
- Number of approved merge requests (collaboration)
- Number of reviews
"""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    User,
    Pamphlet,
    Review,
    Fork,
    MergeRequest,
    MergeRequestStatus,
)


class CredentialService:
    """Service for calculating and updating teacher credentials."""

    # Weights for each component of the credential score
    PAMPHLET_WEIGHT = 5.0
    RATING_WEIGHT = 10.0
    FORK_WEIGHT = 3.0
    MERGE_WEIGHT = 2.0
    REVIEW_COUNT_WEIGHT = 0.5

    @staticmethod
    def calculate_credential_score(
        pamphlet_count: int,
        average_rating: float,
        total_reviews: int,
        forks_received: int,
        merges_approved: int,
    ) -> float:
        """
        Calculate a composite credential score (0-100).

        The score is a weighted sum of various teacher activity metrics.
        """
        # Each rating out of 5 contributes proportionally
        rating_score = (average_rating / 5.0) * CredentialService.RATING_WEIGHT
        review_count_score = min(total_reviews, 20) * CredentialService.REVIEW_COUNT_WEIGHT
        pamphlet_score = min(pamphlet_count, 10) * CredentialService.PAMPHLET_WEIGHT
        fork_score = min(forks_received, 10) * CredentialService.FORK_WEIGHT
        merge_score = min(merges_approved, 10) * CredentialService.MERGE_WEIGHT

        total = (
            pamphlet_score
            + rating_score
            + review_count_score
            + fork_score
            + merge_score
        )
        return min(round(total, 2), 100.0)

    @staticmethod
    def compute_user_metrics(db: Session, user_id: UUID) -> dict:
        """
        Compute all credential metrics for a user from the database.
        """
        # Pamphlet count
        pamphlet_count = (
            db.query(func.count(Pamphlet.id))
            .filter(Pamphlet.author_id == user_id)
            .scalar() or 0
        )

        # Reviews received on user's pamphlets
        user_pamphlets = (
            db.query(Pamphlet.id).filter(Pamphlet.author_id == user_id).subquery()
        )
        rating_stats = (
            db.query(
                func.count(Review.id).label("total"),
                func.avg(Review.rating).label("avg"),
            )
            .filter(Review.pamphlet_id.in_(user_pamphlets))
            .first()
        )
        total_reviews = rating_stats.total or 0
        average_rating = float(rating_stats.avg or 0.0)

        # Forks received on user's pamphlets
        forks_received = (
            db.query(func.count(Fork.id))
            .filter(Fork.original_pamphlet_id.in_(user_pamphlets))
            .scalar() or 0
        )

        # Approved merges by user
        merges_approved = (
            db.query(func.count(MergeRequest.id))
            .filter(
                MergeRequest.created_by == user_id,
                MergeRequest.status == MergeRequestStatus.APPROVED,
            )
            .scalar() or 0
        )

        return {
            "pamphlet_count": pamphlet_count,
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "forks_received": forks_received,
            "merges_approved": merges_approved,
        }

    @staticmethod
    def update_user_credential(db: Session, user_id: UUID) -> User:
        """
        Recalculate and update the credential score for a user.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        metrics = CredentialService.compute_user_metrics(db, user_id)

        user.pamphlet_count = metrics["pamphlet_count"]
        user.total_reviews = metrics["total_reviews"]
        user.average_rating = metrics["average_rating"]
        user.forks_received = metrics["forks_received"]
        user.merges_approved = metrics["merges_approved"]
        user.credential_score = CredentialService.calculate_credential_score(
            metrics["pamphlet_count"],
            metrics["average_rating"],
            metrics["total_reviews"],
            metrics["forks_received"],
            metrics["merges_approved"],
        )

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_top_teachers(db: Session, limit: int = 10) -> list[User]:
        """
        Get the top teachers by credential score.
        """
        return (
            db.query(User)
            .order_by(User.credential_score.desc())
            .limit(limit)
            .all()
        )

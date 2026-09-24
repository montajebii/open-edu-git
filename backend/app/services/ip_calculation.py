"""
Intellectual Property percentage calculation service for OpenEdu Git.

IP% represents the percentage of content ownership for each contributor
to a pamphlet. This is used to track attribution and display IP percentages.
"""

from uuid import UUID

from sqlalchemy import Float, func
from sqlalchemy.orm import Session

from app.db.models import Pamphlet, PamphletVersion, Fork, MergeRequest, MergeRequestStatus


class IPCalculationService:
    """
    Service for calculating intellectual property percentages.

    IP% Algorithm:
    - Original author starts at 100%
    - Each fork reduces the original author's IP% and gives the forked_author
      a portion based on contributions
    - Merget requests that are approved transfer IP% from source to target
    - The total should always sum to 100%
    """

    @staticmethod
    def calculate_pamphlet_ip_distribution(
        db: Session, pamphlet_id: UUID
    ) -> dict[UUID, float]:
        """
        Calculate the IP percentage distribution for all contributors to a pamphlet.

        Returns a dict mapping contributor_user_id -> IP percentage.
        """
        pamphlet = db.query(Pamphlet).filter(Pamphlet.id == pamphlet_id).first()
        if not pamphlet:
            return {}

        distribution: dict[UUID, float] = {}

        # Original author gets the stored percentage
        distribution[pamphlet.author_id] = pamphlet.original_author_ip_percentage or 100.0

        # Add IP from forked pamphlets that contributed via merge requests
        merge_requests = (
            db.query(MergeRequest)
            .filter(
                MergeRequest.target_pamphlet_id == pamphlet_id,
                MergeRequest.status == MergeRequestStatus.APPROVED,
            )
            .all()
        )

        total_approved_merges = len(merge_requests)
        if total_approved_merges > 0:
            # Each approved merge reduces original author IP and distributes among contributors
            ip_per_merge = (100.0 - (pamphlet.original_author_ip_percentage or 100.0)) / total_approved_merges
            for mr in merge_requests:
                contributor_id = mr.created_by
                if contributor_id not in distribution:
                    distribution[contributor_id] = 0.0
                distribution[contributor_id] += ip_per_merge

        return distribution

    @staticmethod
    def get_user_ip_percentage(db: Session, pamphlet_id: UUID, user_id: UUID) -> float:
        """
        Get the IP percentage for a specific user on a specific pamphlet.
        """
        distribution = IPCalculationService.calculate_pamphlet_ip_distribution(db, pamphlet_id)
        return distribution.get(user_id, 0.0)

    @staticmethod
    def update_ip_after_merge(
        db: Session, target_pamphlet_id: UUID, contributor_id: UUID, contribution_weight: float = 10.0
    ) -> None:
        """
        Update IP percentages after a merge request is approved.

        Args:
            db: Database session
            target_pamphlet_id: The pamphlet that received the merge
            contributor_id: The user who contributed via merge
            contribution_weight: Percentage points to transfer (default 10%)
        """
        pamphlet = db.query(Pamphlet).filter(Pamphlet.id == target_pamphlet_id).first()
        if not pamphlet:
            return

        current_original_ip = pamphlet.original_author_ip_percentage or 100.0
        new_original_ip = max(0.0, current_original_ip - contribution_weight)
        pamphlet.original_author_ip_percentage = new_original_ip
        db.add(pamphlet)
        db.commit()

    @staticmethod
    def calculate_user_total_ip(db: Session, user_id: UUID) -> float:
        """
        Calculate the total IP percentage a user owns across all public pamphlets.
        Returns a number representing total IP ownership points.
        """
        total_ip = 0.0

        # Directly authored pamphlets
        authored = db.query(Pamphlet).filter(Pamphlet.author_id == user_id, Pamphlet.is_public == True).all()
        for p in authored:
            total_ip += p.original_author_ip_percentage or 100.0

        # IP from approved merge requests
        approved_merges = (
            db.query(MergeRequest)
            .filter(
                MergeRequest.created_by == user_id,
                MergeRequest.status == MergeRequestStatus.APPROVED,
            )
            .all()
        )
        for mr in approved_merges:
            total_ip += 10.0  # Each merge contributes 10% IP to target

        return total_ip

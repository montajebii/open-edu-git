"""
Fork and Merge Request API endpoints for OpenEdu Git.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.minio_client import create_pamphlet_version_from_existing
from app.db.session import get_db
from app.models.pamphlet import (
    MergeRequest,
    MergeRequestStatus,
    Pamphlet,
    PamphletFork,
    PamphletVersion,
)
from app.schemas.pamphlet import (
    MergeRequestCreate,
    MergeRequestUpdate,
    PamphletCreate,
    PamphletForkCreate,
)
from app.schemas.user import User

router = APIRouter()


@router.post(
    "/pamphlets/{pamphlet_id}/fork",
    response_model=PamphletForkCreate,
    status_code=status.HTTP_201_CREATED,
)
def create_fork(
    pamphlet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fork a pamphlet: create a new pamphlet with the latest version of the original.

    - Only public pamphlets can be forked.
    - The new pamphlet will have the same metadata as the original.
    - The latest version of the original pamphlet will be copied to the new pamphlet.
    """
    # Get original pamphlet
    original = db.query(Pamphlet).filter(Pamphlet.id == pamphlet_id, Pamphlet.is_public).first()
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pamphlet not found or not public",
        )

    # Get latest version
    latest_version = (
        db.query(PamphletVersion)
        .filter(PamphletVersion.pamphlet_id == pamphlet_id)
        .order_by(PamphletVersion.version_number.desc())
        .first()
    )
    if not latest_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pamphlet has no versions to fork",
        )

    # Create new pamphlet with same metadata
    new_pamphlet_data = PamphletCreate(
        title=f"{original.title} (کپی)",
        grade=original.grade,
        subject=original.subject,
        chapter=original.chapter,
        method=original.method,
        difficulty=original.difficulty,
        is_public=True,
        tags=original.tags,
    )

    new_pamphlet = Pamphlet(**new_pamphlet_data.model_dump(), author_id=current_user.id)
    db.add(new_pamphlet)
    db.flush()  # To get new_pamphlet.id

    # Copy version
    create_pamphlet_version_from_existing(
        db=db,
        original_version=latest_version,
        new_pamphlet_id=new_pamphlet.id,
        created_by=current_user.id,
    )

    # Create fork record
    fork = PamphletFork(
        original_pamphlet_id=original.id,
        forked_by=current_user.id,
        new_pamphlet_id=new_pamphlet.id,
    )
    db.add(fork)
    db.commit()
    db.refresh(fork)

    return fork


@router.post("/merge-requests", response_model=MergeRequest, status_code=status.HTTP_201_CREATED)
def create_merge_request(
    merge_request: MergeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a merge request from a source pamphlet to a target pamphlet.

    - The source pamphlet must be a fork of the target pamphlet (or vice versa).
    - Only the owner of the target pamphlet or designated reviewers can approve.
    """
    # Check source and target exist
    source = db.query(Pamphlet).filter(Pamphlet.id == merge_request.source_pamphlet_id).first()
    target = db.query(Pamphlet).filter(Pamphlet.id == merge_request.target_pamphlet_id).first()

    if not source or not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source or target pamphlet not found",
        )

    # Check if source is a fork of target or vice versa
    is_fork = (
        db.query(PamphletFork)
        .filter(
            (
                (PamphletFork.original_pamphlet_id == source.id)
                & (PamphletFork.new_pamphlet_id == target.id)
            )
            | (
                (PamphletFork.original_pamphlet_id == target.id)
                & (PamphletFork.new_pamphlet_id == source.id)
            )
        )
        .first()
    )

    if not is_fork:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source pamphlet is not a fork of target pamphlet",
        )

    # Create merge request
    db_merge_request = MergeRequest(
        source_pamphlet_id=merge_request.source_pamphlet_id,
        target_pamphlet_id=merge_request.target_pamphlet_id,
        title=merge_request.title,
        description=merge_request.description,
        created_by=current_user.id,
    )
    db.add(db_merge_request)
    db.commit()
    db.refresh(db_merge_request)

    return db_merge_request


@router.get("/pamphlets/{pamphlet_id}/merge-requests", response_model=list[MergeRequest])
def get_pamphlet_merge_requests(
    pamphlet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all merge requests for a pamphlet (sent or received).

    - Only the owner of the pamphlet or the creator of the merge request can see it.
    """
    # Check pamphlet exists
    pamphlet = db.query(Pamphlet).filter(Pamphlet.id == pamphlet_id).first()
    if not pamphlet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pamphlet not found",
        )

    # Only return merge requests where current user is owner of source or target, or creator
    merge_requests = (
        db.query(MergeRequest)
        .filter(
            (
                (MergeRequest.source_pamphlet_id == pamphlet_id)
                | (MergeRequest.target_pamphlet_id == pamphlet_id)
            )
            & (
                (MergeRequest.created_by == current_user.id)
                | (
                    MergeRequest.source_pamphlet_id.in_(
                        db.query(Pamphlet.id).filter(Pamphlet.author_id == current_user.id)
                    )
                )
                | (
                    MergeRequest.target_pamphlet_id.in_(
                        db.query(Pamphlet.id).filter(Pamphlet.author_id == current_user.id)
                    )
                )
            )
        )
        .all()
    )

    return merge_requests


@router.patch("/merge-requests/{merge_request_id}", response_model=MergeRequest)
def update_merge_request(
    merge_request_id: int,
    update_data: MergeRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a merge request (approve/reject).

    - Only the owner of the target pamphlet can approve/reject.
    - On approve: create a new version on the target pamphlet with the content from source.
    """
    # Get merge request
    merge_request = db.query(MergeRequest).filter(MergeRequest.id == merge_request_id).first()
    if not merge_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merge request not found",
        )

    # Check if current user is owner of target pamphlet
    target_pamphlet = (
        db.query(Pamphlet).filter(Pamphlet.id == merge_request.target_pamphlet_id).first()
    )
    if not target_pamphlet or target_pamphlet.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner of the target pamphlet can update this merge request",
        )

    # Check status transition is valid
    if merge_request.status != MergeRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Merge request is already closed",
        )

    # Update status
    merge_request.status = update_data.status
    merge_request.reviewed_by = current_user.id
    merge_request.reviewed_at = datetime.utcnow()

    if update_data.status == MergeRequestStatus.APPROVED:
        # Get latest version from source
        source_version = (
            db.query(PamphletVersion)
            .filter(PamphletVersion.pamphlet_id == merge_request.source_pamphlet_id)
            .order_by(PamphletVersion.version_number.desc())
            .first()
        )

        if not source_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source pamphlet has no versions",
            )

        # Create new version on target
        create_pamphlet_version_from_existing(
            db=db,
            original_version=source_version,
            new_pamphlet_id=merge_request.target_pamphlet_id,
            created_by=current_user.id,
        )

    db.commit()
    db.refresh(merge_request)

    return merge_request

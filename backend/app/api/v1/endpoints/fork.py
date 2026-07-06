"""
Pamphlet fork and merge request endpoints.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pamphlet import (
    MergeRequest as MergeRequestModel,
    MergeRequestStatus,
    Pamphlet as PamphletModel,
    PamphletFork as PamphletForkModel,
    PamphletVersion as PamphletVersionModel,
)
from app.models.user import User as UserModel
from app.schemas.pamphlet import (
    MergeRequest,
    MergeRequestCreate,
    MergeRequestReview,
    PamphletFork,
)

router = APIRouter()


def _latest_version(db: Session, pamphlet_id: int) -> Optional[PamphletVersionModel]:
    return (
        db.query(PamphletVersionModel)
        .filter(PamphletVersionModel.pamphlet_id == pamphlet_id)
        .order_by(PamphletVersionModel.version_number.desc())
        .first()
    )


def _create_version_from_existing(
    db: Session,
    source_version: PamphletVersionModel,
    target_pamphlet_id: int,
    author_id: int,
) -> PamphletVersionModel:
    latest_target = _latest_version(db, target_pamphlet_id)
    next_number = 1 if latest_target is None else latest_target.version_number + 1
    version = PamphletVersionModel(
        pamphlet_id=target_pamphlet_id,
        version_number=next_number,
        file_path=source_version.file_path,
        file_type=source_version.file_type,
        file_size=source_version.file_size,
        notes=f"Copied from pamphlet {source_version.pamphlet_id} version {source_version.version_number}",
        author_id=author_id,
    )
    db.add(version)
    return version


@router.post("/pamphlets/{pamphlet_id}/fork", response_model=PamphletFork, status_code=status.HTTP_201_CREATED)
def fork_pamphlet(
    pamphlet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a fork of a public pamphlet."""
    original = (
        db.query(PamphletModel)
        .filter(PamphletModel.id == pamphlet_id, PamphletModel.is_public == 1)
        .first()
    )
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")

    latest_version = _latest_version(db, original.id)
    if latest_version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pamphlet has no versions")

    forked_pamphlet = PamphletModel(
        title=f"{original.title} (fork)",
        author_id=current_user.id,
        grade=original.grade,
        subject=original.subject,
        chapter=original.chapter,
        method=original.method,
        difficulty=original.difficulty,
        is_public=1,
        tags=original.tags,
    )
    db.add(forked_pamphlet)
    db.flush()

    _create_version_from_existing(db, latest_version, forked_pamphlet.id, current_user.id)

    fork = PamphletForkModel(
        original_pamphlet_id=original.id,
        forked_by=current_user.id,
        new_pamphlet_id=forked_pamphlet.id,
    )
    db.add(fork)
    db.commit()
    db.refresh(fork)
    return fork


@router.post(
    "/pamphlets/{pamphlet_id}/merge-requests",
    response_model=MergeRequest,
    status_code=status.HTTP_201_CREATED,
)
def create_merge_request(
    pamphlet_id: int,
    merge_request: MergeRequestCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a merge request from a fork into the target pamphlet."""
    target = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    source = db.query(PamphletModel).filter(PamphletModel.id == merge_request.source_pamphlet_id).first()
    if not target or not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")
    if source.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only fork author can create merge request")

    fork = (
        db.query(PamphletForkModel)
        .filter(
            PamphletForkModel.original_pamphlet_id == target.id,
            PamphletForkModel.new_pamphlet_id == source.id,
        )
        .first()
    )
    if not fork:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source is not a fork of target")

    open_request = (
        db.query(MergeRequestModel)
        .filter(
            MergeRequestModel.source_pamphlet_id == source.id,
            MergeRequestModel.target_pamphlet_id == target.id,
            MergeRequestModel.status == MergeRequestStatus.PENDING,
        )
        .first()
    )
    if open_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Open merge request already exists")

    db_request = MergeRequestModel(
        source_pamphlet_id=source.id,
        target_pamphlet_id=target.id,
        title=merge_request.title,
        description=merge_request.description,
        created_by=current_user.id,
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@router.get("/pamphlets/{pamphlet_id}/merge-requests", response_model=List[MergeRequest])
def list_merge_requests(
    pamphlet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List merge requests for pamphlets owned by current user or created by current user."""
    pamphlet = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    if not pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")

    query = db.query(MergeRequestModel).filter(
        (MergeRequestModel.source_pamphlet_id == pamphlet_id)
        | (MergeRequestModel.target_pamphlet_id == pamphlet_id)
    )
    if pamphlet.author_id != current_user.id:
        query = query.filter(MergeRequestModel.created_by == current_user.id)
    return query.order_by(MergeRequestModel.created_at.desc()).all()


@router.post("/merge-requests/{merge_request_id}/approve", response_model=MergeRequest)
def approve_merge_request(
    merge_request_id: int,
    review: MergeRequestReview = MergeRequestReview(),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Approve a merge request and add source latest file as target new version."""
    merge_request = db.query(MergeRequestModel).filter(MergeRequestModel.id == merge_request_id).first()
    if not merge_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merge request not found")
    if merge_request.status != MergeRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merge request already closed")

    target = db.query(PamphletModel).filter(PamphletModel.id == merge_request.target_pamphlet_id).first()
    if not target or target.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only target author can approve")

    source_version = _latest_version(db, merge_request.source_pamphlet_id)
    if source_version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source pamphlet has no versions")

    _create_version_from_existing(db, source_version, target.id, current_user.id)
    merge_request.status = MergeRequestStatus.APPROVED
    merge_request.reviewed_by = current_user.id
    merge_request.reviewed_at = datetime.utcnow()
    merge_request.review_note = review.review_note
    db.commit()
    db.refresh(merge_request)
    return merge_request


@router.post("/merge-requests/{merge_request_id}/reject", response_model=MergeRequest)
def reject_merge_request(
    merge_request_id: int,
    review: MergeRequestReview = MergeRequestReview(),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Reject a merge request."""
    merge_request = db.query(MergeRequestModel).filter(MergeRequestModel.id == merge_request_id).first()
    if not merge_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merge request not found")
    if merge_request.status != MergeRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merge request already closed")

    target = db.query(PamphletModel).filter(PamphletModel.id == merge_request.target_pamphlet_id).first()
    if not target or target.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only target author can reject")

    merge_request.status = MergeRequestStatus.REJECTED
    merge_request.reviewed_by = current_user.id
    merge_request.reviewed_at = datetime.utcnow()
    merge_request.review_note = review.review_note
    db.commit()
    db.refresh(merge_request)
    return merge_request

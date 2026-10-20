"""
API v1 routers for OpenEdu Git.

Every router lives in ``app.api.v1.endpoints``; this module is the only place
that wires them together.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, fork, pamphlet, review, storage, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(pamphlet.router, prefix="/pamphlets", tags=["pamphlets"])
api_router.include_router(review.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(fork.router, tags=["forks"])
api_router.include_router(storage.router)

__all__ = ["api_router"]

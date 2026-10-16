"""
API v1 routers for OpenEdu Git.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, credentials, fork, pamphlet, review, storage, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(pamphlet.router, prefix="/pamphlets", tags=["pamphlets"])
api_router.include_router(review.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(fork.router, tags=["forks"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(credentials.router, tags=["credentials"])
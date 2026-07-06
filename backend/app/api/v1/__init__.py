"""
API v1 routers for OpenEdu Git.
"""

from fastapi import APIRouter
from app.api.v1 import auth, pamphlet

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(pamphlet.router, prefix="/pamphlets", tags=["pamphlets"])
"""
API v1 routers for OpenEdu Git.
"""

from fastapi import APIRouter
from app.api.v1 import auth, endpoints
from app.api.v1.endpoints import pamphlet, review

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
"""
OpenEdu Git Backend - FastAPI Application
"""

from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import api_router
from .api.v1.endpoints import fork, pamphlet, review

app = FastAPI(
    title="OpenEdu Git API",
    description="API for the OpenEdu Git platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Set up CORS
origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers for frontend
)


# Include API routers

api_router.include_router(pamphlet.router, prefix="/pamphlets", tags=["pamphlets"])
api_router.include_router(review.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(fork.router, tags=["forks"])
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to OpenEdu Git API"}

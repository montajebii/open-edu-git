"""
OpenEdu Git Backend - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from .api.v1 import api_router

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
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "Welcome to OpenEdu Git API"}

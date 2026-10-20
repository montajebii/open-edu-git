"""
OpenEdu Git Backend - FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.minio_client import ensure_buckets

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Prepare optional infrastructure without blocking start-up."""
    ensure_buckets()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the OpenEdu Git platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["meta"])
def read_root():
    return {"message": "Welcome to OpenEdu Git API"}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

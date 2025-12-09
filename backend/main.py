"""
FastAPI Application Entry Point

Main application configuration and initialization.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.dependencies import engine
from backend.api.routes import video
from backend.models.video import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Key-Face-Frame API",
    description="Video keyframe extraction service with person detection",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

# Include routers
app.include_router(video.router, prefix="/api", tags=["videos"])

# Mount static files for serving keyframe images
output_dir = Path("output").absolute()
output_dir.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=str(output_dir)), name="output_files")
logger.info(f"Static files mounted at /files -> {output_dir}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Key-Face-Frame API starting up...")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Key-Face-Frame API shutting down...")

"""
Video Processing Routes

FastAPI endpoints for video upload, processing, and keyframe retrieval.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.schemas.video import (
    KeyframeInfo,
    ProcessingConfig,
    VideoStatusResponse,
    VideoUploadResponse,
)
from backend.core.config import settings
from backend.models.video import Video
from backend.workers.tasks import process_video_task

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/videos/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    sample_rate: int = Form(default=1),
    max_frames: int = Form(default=100),
    confidence_threshold: float = Form(default=0.5),
    db: Session = Depends(get_db),
):
    """
    Upload video and start processing.

    Steps:
    1. Validate file (format, size)
    2. Save to disk
    3. Create database record
    4. Queue Celery task
    5. Return video_id

    Args:
        file: Uploaded video file
        sample_rate: Frame sampling rate (1-10)
        max_frames: Maximum keyframes to extract (10-500)
        confidence_threshold: Detection confidence threshold (0.1-0.9)
        db: Database session

    Returns:
        VideoUploadResponse with video_id and status

    Raises:
        HTTPException: If file validation fails
    """
    logger.info(f"Uploading video: {file.filename}")

    # 1. Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    # 2. Validate processing config
    try:
        config = ProcessingConfig(
            sample_rate=sample_rate,
            max_frames=max_frames,
            confidence_threshold=confidence_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 3. Generate unique video ID
    video_id = str(uuid.uuid4())

    # 4. Save file to upload directory
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = settings.upload_dir / f"{video_id}{file_ext}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save video file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save video file")

    # 5. Create database record
    video = Video(
        id=video_id, filename=file.filename, file_path=str(file_path), status="pending", progress=0
    )
    db.add(video)
    db.commit()

    # 6. Queue Celery task
    try:
        task = process_video_task.delay(
            video_id=video_id,
            video_path=str(file_path),
            config={
                "sample_rate": config.sample_rate,
                "max_frames": config.max_frames,
                "confidence_threshold": config.confidence_threshold,
            },
        )
        logger.info(f"Queued processing task: video_id={video_id}, task_id={task.id}")
    except Exception as e:
        logger.error(f"Failed to queue task: {e}")
        # Clean up
        video.status = "failed"
        video.error_message = f"Failed to queue task: {e}"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to start processing")

    return VideoUploadResponse(
        video_id=video_id,
        filename=file.filename,
        status="pending",
        message=f"Video queued for processing. Use video_id '{video_id}' to check status.",
    )


@router.get("/videos/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, db: Session = Depends(get_db)):
    """
    Get video processing status.

    Returns current status, progress, and results (if completed).

    Args:
        video_id: Video identifier
        db: Database session

    Returns:
        VideoStatusResponse with current status

    Raises:
        HTTPException: If video not found
    """
    logger.debug(f"Getting status for video: {video_id}")

    # Query video record
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    # Convert keyframes JSON to KeyframeInfo objects
    keyframes = None
    if video.keyframes:
        keyframes = [KeyframeInfo(**kf) for kf in video.keyframes]

    return VideoStatusResponse(
        video_id=video.id,
        filename=video.filename,
        status=video.status,
        progress=video.progress,
        stage=video.stage,
        total_frames=video.total_frames,
        total_detections=video.total_detections,
        keyframes_extracted=video.keyframes_extracted,
        processing_time_seconds=video.processing_time_seconds,
        output_dir=video.output_dir,
        metadata_path=video.metadata_path,
        keyframes=keyframes,
        error_message=video.error_message,
        created_at=video.created_at,
        started_at=video.started_at,
        completed_at=video.completed_at,
    )


@router.get("/videos/{video_id}/keyframes")
async def get_keyframes(video_id: str, db: Session = Depends(get_db)):
    """
    Get keyframe images metadata.

    Returns JSON with keyframe information including file paths.
    For MVP: returns file paths.
    Future: could serve images directly or S3 URLs.

    Args:
        video_id: Video identifier
        db: Database session

    Returns:
        JSON with keyframes list

    Raises:
        HTTPException: If video not found or not completed
    """
    logger.debug(f"Getting keyframes for video: {video_id}")

    # Query video record
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    if video.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Video processing not completed. Current status: {video.status}",
        )

    if not video.keyframes:
        return {"video_id": video_id, "count": 0, "keyframes": []}

    return {
        "video_id": video_id,
        "count": len(video.keyframes),
        "keyframes": video.keyframes,
        "output_dir": video.output_dir,
    }

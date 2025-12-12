"""
Celery Tasks

Asynchronous video processing tasks.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from celery import Celery, Task

from backend.api.dependencies import SessionLocal
from backend.core.agents.detection_agent import DetectionAgent
from backend.core.agents.keyframe_agent import KeyframeAgent
from backend.core.agents.lead_agent import LeadAgent
from backend.core.config import settings
from backend.models.video import Video

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "keyframe_extraction", broker=settings.celery_broker_url, backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True)
def process_video_task(
    self: Task, video_id: str, video_path: str, config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Celery task to process video.

    Updates database status at each stage:
    - detection (0-50%)
    - extraction (50-100%)

    Args:
        self: Celery task instance
        video_id: Unique video identifier
        video_path: Path to video file
        config: Processing configuration
            - sample_rate: int
            - max_frames: int
            - confidence_threshold: float

    Returns:
        Dict containing processing results or error information
    """
    logger.info(f"Starting video processing task: video_id={video_id}")

    # Get database session
    db = SessionLocal()

    try:
        # Get video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        # Update status to processing
        video.status = "processing"
        video.started_at = datetime.now(timezone.utc)  # Use timezone-aware datetime
        video.progress = 0
        db.commit()

        # Define progress callback
        def progress_callback(stage: str, progress: int) -> None:
            """Update database with progress."""
            video.stage = stage
            video.progress = progress
            db.commit()
            logger.info(f"Progress update: {video_id} - {stage}: {progress}%")

        # Initialize agents
        detection_agent = DetectionAgent(model_name=settings.yolo_model)
        keyframe_agent = KeyframeAgent(output_dir=settings.output_dir)
        lead_agent = LeadAgent(
            detection_agent=detection_agent,
            keyframe_agent=keyframe_agent,
            default_config={
                "sample_rate": config.get("sample_rate", settings.default_sample_rate),
                "max_frames": config.get("max_frames", settings.default_max_frames),
                "confidence_threshold": config.get(
                    "confidence_threshold", settings.default_confidence_threshold
                ),
            },
        )

        # Process video (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                lead_agent.process_video(
                    video_path=Path(video_path),
                    video_id=video_id,
                    config=config,
                    progress_callback=progress_callback,
                )
            )
        finally:
            loop.close()

        # Update video record with results
        video.status = "completed"
        video.progress = 100
        video.stage = "complete"
        video.completed_at = datetime.now(timezone.utc)  # Use timezone-aware datetime
        video.total_frames = result.total_frames
        video.total_detections = result.total_detections
        video.keyframes_extracted = result.keyframes_extracted
        video.processing_time_seconds = result.processing_time_seconds
        video.output_dir = str(result.output_dir)
        video.metadata_path = str(result.metadata_path)
        video.keyframes = result.keyframes
        db.commit()

        logger.info(f"Video processing completed: video_id={video_id}")

        return {
            "video_id": video_id,
            "status": "completed",
            "total_frames": result.total_frames,
            "total_detections": result.total_detections,
            "keyframes_extracted": result.keyframes_extracted,
            "processing_time_seconds": result.processing_time_seconds,
        }

    except Exception as e:
        logger.error(f"Video processing failed: video_id={video_id}, error={e}", exc_info=True)

        # Update video status to failed
        video.status = "failed"
        video.error_message = str(e)
        video.completed_at = datetime.now(timezone.utc)  # Use timezone-aware datetime
        db.commit()

        return {"video_id": video_id, "status": "failed", "error_message": str(e)}

    finally:
        db.close()

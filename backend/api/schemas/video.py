"""
Video Schemas

Pydantic models for video processing requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    """Response after uploading video."""

    video_id: str
    filename: str
    status: str
    message: str

    class Config:
        from_attributes = True


class KeyframeInfo(BaseModel):
    """Individual keyframe metadata."""

    frame_index: int
    timestamp: float
    score: float
    bbox: List[float]
    filename: str

    class Config:
        from_attributes = True


class VideoStatusResponse(BaseModel):
    """Video processing status response."""

    video_id: str
    filename: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    stage: Optional[str] = None

    # Results (if completed)
    total_frames: Optional[int] = None
    total_detections: Optional[int] = None
    keyframes_extracted: Optional[int] = None
    processing_time_seconds: Optional[float] = None

    # Output paths (if completed)
    output_dir: Optional[str] = None
    metadata_path: Optional[str] = None

    # Keyframes (if completed)
    keyframes: Optional[List[KeyframeInfo]] = None

    # Error (if failed)
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessingConfig(BaseModel):
    """Processing configuration parameters."""

    sample_rate: int = Field(default=1, ge=1, le=10, description="Frame sampling rate")
    max_frames: int = Field(default=100, ge=10, le=500, description="Maximum keyframes to extract")
    confidence_threshold: float = Field(
        default=0.5, ge=0.1, le=0.9, description="Detection confidence threshold"
    )

    class Config:
        from_attributes = True

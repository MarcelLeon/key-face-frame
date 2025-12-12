"""
Video Models

SQLAlchemy ORM models for video processing data.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Video(Base):
    """
    Video processing job model.

    Stores all metadata for a video processing job including:
    - File information (filename, path)
    - Status tracking (status, progress, stage)
    - Results (frame counts, keyframes, processing time)
    - Output paths (output_dir, metadata_path)
    - Error tracking (error_message)
    - Timestamps (created_at, started_at, completed_at)
    """

    __tablename__ = "videos"

    # Primary key
    id = Column(String, primary_key=True)  # UUID

    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    # Status tracking
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    stage = Column(String, nullable=True)  # detection, extraction, complete

    # Results
    total_frames = Column(Integer, nullable=True)
    total_detections = Column(Integer, nullable=True)
    keyframes_extracted = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Paths
    output_dir = Column(String, nullable=True)
    metadata_path = Column(String, nullable=True)

    # Error handling
    error_message = Column(String, nullable=True)

    # Timestamps (using timezone-aware UTC datetime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Keyframes (JSON array)
    keyframes = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, filename={self.filename}, status={self.status})>"

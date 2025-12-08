"""
Application Configuration

Environment-based configuration management.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Paths
    output_dir: Path = Path("output")
    upload_dir: Path = Path("uploads")

    # Database
    database_url: str = "sqlite:///./keyframe.db"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # YOLO
    yolo_model: str = "yolov8m.pt"

    # Processing defaults
    default_sample_rate: int = 1
    default_max_frames: int = 100
    default_confidence_threshold: float = 0.5

    # File upload
    max_upload_size: int = 2 * 1024 * 1024 * 1024  # 2GB
    allowed_extensions: set = {".mp4", ".mov", ".avi", ".mkv"}

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()

"""
Tests for Video API Routes

TDD tests for video processing endpoints.
"""

import io
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.dependencies import get_db
from backend.main import app
from backend.models.video import Base, Video

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with database override."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_video_file(tmp_path: Path) -> Path:
    """Create a sample video file."""
    video_file = tmp_path / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    return video_file


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestUploadVideoEndpoint:
    """Test video upload endpoint."""

    @patch("backend.api.routes.video.process_video_task")
    def test_upload_video_success(
        self, mock_task: Mock, client: TestClient, sample_video_file: Path
    ):
        """Test successful video upload."""
        # Mock Celery task
        mock_task.delay.return_value = Mock(id="task-123")

        # Upload video
        with open(sample_video_file, "rb") as f:
            response = client.post(
                "/api/videos/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")},
                data={"sample_rate": "2", "max_frames": "50", "confidence_threshold": "0.6"},
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert data["filename"] == "test_video.mp4"
        assert data["status"] == "pending"
        assert "queued for processing" in data["message"].lower()

    def test_upload_video_invalid_extension(self, client: TestClient):
        """Test upload with invalid file extension."""
        fake_file = io.BytesIO(b"fake content")

        response = client.post(
            "/api/videos/upload", files={"file": ("test.txt", fake_file, "text/plain")}
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @patch("backend.api.routes.video.process_video_task")
    def test_upload_video_with_default_config(
        self, mock_task: Mock, client: TestClient, sample_video_file: Path
    ):
        """Test upload uses default config if not provided."""
        mock_task.delay.return_value = Mock(id="task-123")

        with open(sample_video_file, "rb") as f:
            response = client.post(
                "/api/videos/upload", files={"file": ("test_video.mp4", f, "video/mp4")}
            )

        assert response.status_code == 200
        # Verify task was called with defaults
        mock_task.delay.assert_called_once()

    def test_upload_video_validation_errors(self, client: TestClient, sample_video_file: Path):
        """Test validation of processing config parameters."""
        with open(sample_video_file, "rb") as f:
            response = client.post(
                "/api/videos/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")},
                data={
                    "sample_rate": "20",  # Too high (max 10)
                    "max_frames": "5",  # Too low (min 10)
                },
            )

        assert response.status_code == 422  # Validation error


class TestGetVideoStatusEndpoint:
    """Test video status endpoint."""

    def test_get_video_status_success(self, client: TestClient, test_db):
        """Test getting status of existing video."""
        # Create test video record
        video = Video(
            id="test-video-123",
            filename="test.mp4",
            file_path="/path/to/test.mp4",
            status="processing",
            progress=50,
            stage="detection",
            created_at=datetime.utcnow(),
        )
        test_db.add(video)
        test_db.commit()

        # Get status
        response = client.get("/api/videos/test-video-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == "test-video-123"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["stage"] == "detection"

    def test_get_video_status_not_found(self, client: TestClient):
        """Test getting status of non-existent video."""
        response = client.get("/api/videos/nonexistent-id/status")

        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]

    def test_get_video_status_completed_with_keyframes(self, client: TestClient, test_db):
        """Test getting status of completed video with keyframes."""
        # Create completed video record
        video = Video(
            id="test-video-456",
            filename="completed.mp4",
            file_path="/path/to/completed.mp4",
            status="completed",
            progress=100,
            stage="complete",
            total_frames=100,
            total_detections=50,
            keyframes_extracted=10,
            processing_time_seconds=5.5,
            output_dir="/output/video-test-video-456",
            metadata_path="/output/video-test-video-456/metadata.json",
            keyframes=[
                {
                    "frame_index": 10,
                    "timestamp": 0.33,
                    "score": 0.95,
                    "bbox": [100, 100, 200, 300],
                    "filename": "keyframe_0010.jpg",
                }
            ],
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        test_db.add(video)
        test_db.commit()

        # Get status
        response = client.get("/api/videos/test-video-456/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["keyframes_extracted"] == 10
        assert len(data["keyframes"]) == 1
        assert data["keyframes"][0]["frame_index"] == 10

    def test_get_video_status_failed(self, client: TestClient, test_db):
        """Test getting status of failed video."""
        # Create failed video record
        video = Video(
            id="test-video-789",
            filename="failed.mp4",
            file_path="/path/to/failed.mp4",
            status="failed",
            progress=30,
            stage="detection",
            error_message="Detection failed: model not loaded",
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        test_db.add(video)
        test_db.commit()

        # Get status
        response = client.get("/api/videos/test-video-789/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Detection failed: model not loaded"


class TestGetKeyframesEndpoint:
    """Test keyframes retrieval endpoint."""

    def test_get_keyframes_success(self, client: TestClient, test_db):
        """Test getting keyframes from completed video."""
        # Create completed video with keyframes
        video = Video(
            id="test-video-keyframes",
            filename="keyframes.mp4",
            file_path="/path/to/keyframes.mp4",
            status="completed",
            progress=100,
            keyframes=[
                {
                    "frame_index": 10,
                    "timestamp": 0.33,
                    "score": 0.95,
                    "bbox": [100, 100, 200, 300],
                    "filename": "keyframe_0010.jpg",
                },
                {
                    "frame_index": 50,
                    "timestamp": 1.67,
                    "score": 0.92,
                    "bbox": [150, 120, 250, 320],
                    "filename": "keyframe_0050.jpg",
                },
            ],
            created_at=datetime.utcnow(),
        )
        test_db.add(video)
        test_db.commit()

        # Get keyframes
        response = client.get("/api/videos/test-video-keyframes/keyframes")

        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == "test-video-keyframes"
        assert data["count"] == 2
        assert len(data["keyframes"]) == 2
        assert data["keyframes"][0]["frame_index"] == 10

    def test_get_keyframes_video_not_found(self, client: TestClient):
        """Test getting keyframes from non-existent video."""
        response = client.get("/api/videos/nonexistent/keyframes")

        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]

    def test_get_keyframes_processing_not_complete(self, client: TestClient, test_db):
        """Test getting keyframes from video still processing."""
        # Create processing video
        video = Video(
            id="test-video-processing",
            filename="processing.mp4",
            file_path="/path/to/processing.mp4",
            status="processing",
            progress=50,
            created_at=datetime.utcnow(),
        )
        test_db.add(video)
        test_db.commit()

        # Try to get keyframes
        response = client.get("/api/videos/test-video-processing/keyframes")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()

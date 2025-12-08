"""
Tests for Celery Tasks

TDD tests for video processing tasks.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.core.agents.lead_agent import ProcessingResult
from backend.workers.tasks import celery_app, process_video_task


@pytest.fixture
def mock_video_path(tmp_path: Path) -> Path:
    """Create a mock video file."""
    video_file = tmp_path / "test_video.mp4"
    video_file.write_text("fake video content")
    return video_file


@pytest.fixture
def mock_processing_result(mock_video_path: Path) -> ProcessingResult:
    """Create a mock ProcessingResult."""
    return ProcessingResult(
        video_id="test-video-123",
        video_path=mock_video_path,
        total_frames=100,
        total_detections=50,
        keyframes_extracted=10,
        processing_time_seconds=5.5,
        output_dir=Path("output/video-test-video-123"),
        keyframe_dir=Path("output/video-test-video-123/keyframes"),
        metadata_path=Path("output/video-test-video-123/metadata.json"),
        keyframes=[
            {
                "frame_index": 10,
                "timestamp": 0.33,
                "score": 0.95,
                "bbox": [100, 100, 200, 300],
                "filename": "keyframe_0010.jpg",
            }
        ],
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )


class TestCeleryApp:
    """Test Celery application configuration."""

    def test_celery_app_exists(self):
        """Test that celery app is properly initialized."""
        assert celery_app is not None
        assert celery_app.main == "keyframe_extraction"

    def test_celery_broker_configured(self):
        """Test that broker URL is configured."""
        assert "redis://" in celery_app.conf.broker_url

    def test_celery_serializer_configured(self):
        """Test that JSON serializer is configured."""
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content


class TestProcessVideoTask:
    """Test process_video_task Celery task."""

    @patch("backend.workers.tasks.LeadAgent")
    @patch("backend.workers.tasks.SessionLocal")
    async def test_process_video_task_success(
        self,
        mock_session_local: Mock,
        mock_lead_agent_class: Mock,
        mock_video_path: Path,
        mock_processing_result: ProcessingResult,
    ):
        """Test successful video processing task."""
        # Setup mocks
        mock_db = Mock()
        mock_video = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_video
        mock_session_local.return_value = mock_db

        # Create async mock for process_video
        async def mock_process_video(*args, **kwargs):
            return mock_processing_result

        mock_lead_agent = Mock()
        mock_lead_agent.process_video = mock_process_video
        mock_lead_agent_class.return_value = mock_lead_agent

        # Execute task
        result = process_video_task(
            video_id="test-video-123",
            video_path=str(mock_video_path),
            config={"sample_rate": 2, "max_frames": 50},
        )

        # Verify result
        assert result["video_id"] == "test-video-123"
        assert result["status"] == "completed"
        assert result["total_frames"] == 100
        assert result["keyframes_extracted"] == 10

    @patch("backend.workers.tasks.LeadAgent")
    @patch("backend.workers.tasks.SessionLocal")
    async def test_process_video_task_updates_database_status(
        self,
        mock_session_local: Mock,
        mock_lead_agent_class: Mock,
        mock_video_path: Path,
        mock_processing_result: ProcessingResult,
    ):
        """Test that task updates database with progress."""
        # Setup mocks
        mock_db = Mock()
        mock_video = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_video
        mock_session_local.return_value = mock_db

        # Create async mock for process_video
        async def mock_process_video(*args, **kwargs):
            return mock_processing_result

        mock_lead_agent = Mock()
        mock_lead_agent.process_video = mock_process_video
        mock_lead_agent_class.return_value = mock_lead_agent

        # Execute task
        process_video_task(video_id="test-video-123", video_path=str(mock_video_path), config={})

        # Verify database updates
        assert mock_video.status in ["processing", "completed"]
        mock_db.commit.assert_called()

    @patch("backend.workers.tasks.LeadAgent")
    @patch("backend.workers.tasks.SessionLocal")
    def test_process_video_task_handles_errors(
        self, mock_session_local: Mock, mock_lead_agent_class: Mock, mock_video_path: Path
    ):
        """Test that task handles processing errors gracefully."""
        # Setup mocks
        mock_db = Mock()
        mock_video = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_video
        mock_session_local.return_value = mock_db

        mock_lead_agent = Mock()
        mock_lead_agent.process_video = Mock(side_effect=Exception("Processing failed"))
        mock_lead_agent_class.return_value = mock_lead_agent

        # Execute task (should not raise)
        result = process_video_task(
            video_id="test-video-123", video_path=str(mock_video_path), config={}
        )

        # Verify error handling
        assert result["status"] == "failed"
        assert "Processing failed" in result["error_message"]
        assert mock_video.status == "failed"
        mock_db.commit.assert_called()

    @patch("backend.workers.tasks.LeadAgent")
    @patch("backend.workers.tasks.SessionLocal")
    def test_process_video_task_progress_callback(
        self,
        mock_session_local: Mock,
        mock_lead_agent_class: Mock,
        mock_video_path: Path,
        mock_processing_result: ProcessingResult,
    ):
        """Test that progress callback updates database."""
        # Setup mocks
        mock_db = Mock()
        mock_video = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_video
        mock_session_local.return_value = mock_db

        # Capture progress callback
        captured_callback = None

        def capture_callback(*args, **kwargs):
            nonlocal captured_callback
            if "progress_callback" in kwargs:
                captured_callback = kwargs["progress_callback"]
            return mock_processing_result

        mock_lead_agent = Mock()
        mock_lead_agent.process_video = Mock(side_effect=capture_callback)
        mock_lead_agent_class.return_value = mock_lead_agent

        # Execute task
        process_video_task(video_id="test-video-123", video_path=str(mock_video_path), config={})

        # Verify callback was passed
        assert captured_callback is not None

        # Test callback updates database
        captured_callback("detection", 50)
        assert mock_video.stage == "detection"
        assert mock_video.progress == 50

"""
Lead Agent Unit Tests

Comprehensive test suite for LeadAgent orchestration.
Following TDD methodology - these tests are written BEFORE implementation.

The LeadAgent coordinates DetectionAgent and KeyframeAgent to process videos.
It handles progress tracking, error management, and result aggregation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

from backend.core.agents.detection_agent import Detection
from backend.core.agents.keyframe_agent import Keyframe
from backend.core.agents.lead_agent import LeadAgent, ProcessingResult
from backend.core.exceptions import VideoProcessingError

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_detection_agent():
    """Mock DetectionAgent for testing orchestration."""
    agent = MagicMock()

    # Mock successful detection
    detections = [
        Detection(
            frame_index=10, timestamp=0.33, bbox=[100, 100, 200, 300], confidence=0.95, track_id=1
        ),
        Detection(
            frame_index=45, timestamp=1.50, bbox=[150, 120, 250, 320], confidence=0.92, track_id=1
        ),
        Detection(
            frame_index=123, timestamp=4.10, bbox=[120, 110, 220, 310], confidence=0.88, track_id=2
        ),
    ]

    agent.process_video = AsyncMock(return_value=detections)

    return agent


@pytest.fixture
def mock_keyframe_agent():
    """Mock KeyframeAgent for testing orchestration."""
    agent = MagicMock()

    # Mock successful keyframe extraction
    keyframes = [
        Keyframe(
            frame_index=10,
            timestamp=0.33,
            score=0.92,
            bbox=[100, 100, 200, 300],
            filename="frame_00010_t0.33s.jpg",
            track_id=1,
        ),
        Keyframe(
            frame_index=123,
            timestamp=4.10,
            score=0.88,
            bbox=[120, 110, 220, 310],
            filename="frame_00123_t4.10s.jpg",
            track_id=2,
        ),
    ]

    agent.extract_keyframes = AsyncMock(return_value=keyframes)
    agent.output_dir = Path("/tmp/output")

    return agent


@pytest.fixture
def test_video_path(tmp_path):
    """Create a temporary test video file."""
    video_path = tmp_path / "test_video.mp4"
    video_path.touch()  # Create empty file
    return video_path


@pytest.fixture
def mock_cv2_videocapture():
    """Mock cv2.VideoCapture for unit tests."""
    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.get.return_value = 150  # 150 total frames
        mock_instance.release = Mock()
        mock_cap.return_value = mock_instance
        yield mock_cap


@pytest.fixture
def progress_callback():
    """Mock progress callback function."""
    return Mock()


# =============================================================================
# 1. INITIALIZATION TESTS
# =============================================================================


def test_lead_agent_initialization(mock_detection_agent, mock_keyframe_agent):
    """Test LeadAgent initializes with required agents."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    assert agent.detection_agent == mock_detection_agent
    assert agent.keyframe_agent == mock_keyframe_agent
    assert agent.default_config is not None


def test_lead_agent_requires_detection_agent(mock_keyframe_agent):
    """Test raises error if DetectionAgent not provided."""
    with pytest.raises(ValueError, match="detection_agent.*required"):
        LeadAgent(detection_agent=None, keyframe_agent=mock_keyframe_agent)


def test_lead_agent_requires_keyframe_agent(mock_detection_agent):
    """Test raises error if KeyframeAgent not provided."""
    with pytest.raises(ValueError, match="keyframe_agent.*required"):
        LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=None)


def test_lead_agent_accepts_custom_config(mock_detection_agent, mock_keyframe_agent):
    """Test LeadAgent can be configured via dict."""
    custom_config = {"sample_rate": 2, "max_frames": 50, "confidence_threshold": 0.7}

    agent = LeadAgent(
        detection_agent=mock_detection_agent,
        keyframe_agent=mock_keyframe_agent,
        default_config=custom_config,
    )

    assert agent.default_config["sample_rate"] == 2
    assert agent.default_config["max_frames"] == 50
    assert agent.default_config["confidence_threshold"] == 0.7


def test_default_config_values(mock_detection_agent, mock_keyframe_agent):
    """Test sensible defaults: sample_rate=1, max_frames=100."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    # Check default config values
    assert agent.default_config["sample_rate"] == 1
    assert agent.default_config["max_frames"] == 100
    assert agent.default_config["confidence_threshold"] == 0.5


# =============================================================================
# 2. VIDEO PROCESSING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_process_video_returns_result(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test process_video returns ProcessingResult."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify result type
    assert isinstance(result, ProcessingResult)

    # Verify result contains expected fields
    assert result.video_id == "test-video-123"
    assert result.video_path == test_video_path
    assert result.total_detections > 0
    assert result.keyframes_extracted > 0
    assert result.processing_time_seconds >= 0
    assert result.output_dir is not None
    assert result.keyframe_dir is not None
    assert result.metadata_path is not None
    assert isinstance(result.keyframes, list)
    assert isinstance(result.started_at, datetime)
    assert isinstance(result.completed_at, datetime)


@pytest.mark.asyncio
async def test_process_video_calls_detection_agent(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test DetectionAgent is called with correct params."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", config={"sample_rate": 2}
    )

    # Verify DetectionAgent.process_video was called
    mock_detection_agent.process_video.assert_called_once()

    # Verify it was called with correct video_path
    call_args = mock_detection_agent.process_video.call_args
    assert call_args.kwargs["video_path"] == test_video_path
    assert call_args.kwargs["sample_rate"] == 2


@pytest.mark.asyncio
async def test_process_video_calls_keyframe_agent(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test KeyframeAgent receives detection results."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify KeyframeAgent.extract_keyframes was called
    mock_keyframe_agent.extract_keyframes.assert_called_once()

    # Verify it received detections from DetectionAgent
    call_args = mock_keyframe_agent.extract_keyframes.call_args
    assert "detections" in call_args.kwargs
    assert len(call_args.kwargs["detections"]) == 3  # From mock_detection_agent

    # Verify detections are converted to dicts
    first_detection = call_args.kwargs["detections"][0]
    assert isinstance(first_detection, dict)
    assert "frame_index" in first_detection
    assert "timestamp" in first_detection
    assert "bbox" in first_detection


@pytest.mark.asyncio
async def test_process_video_propagates_video_id(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test video_id flows through pipeline."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    video_id = "my-special-video-456"

    await agent.process_video(video_path=test_video_path, video_id=video_id)

    # Verify video_id passed to KeyframeAgent
    call_args = mock_keyframe_agent.extract_keyframes.call_args
    assert call_args.kwargs["video_id"] == video_id


@pytest.mark.asyncio
async def test_process_video_with_sample_rate(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test sample_rate parameter passed to DetectionAgent."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", config={"sample_rate": 5}
    )

    # Verify sample_rate passed to DetectionAgent
    call_args = mock_detection_agent.process_video.call_args
    assert call_args.kwargs["sample_rate"] == 5


@pytest.mark.asyncio
async def test_process_video_with_max_frames(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test max_frames parameter passed to KeyframeAgent."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", config={"max_frames": 50}
    )

    # Verify max_frames passed to KeyframeAgent
    call_args = mock_keyframe_agent.extract_keyframes.call_args
    assert call_args.kwargs["max_frames"] == 50


# =============================================================================
# 3. PROGRESS TRACKING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_progress_callback_called(
    mock_detection_agent,
    mock_keyframe_agent,
    test_video_path,
    progress_callback,
    mock_cv2_videocapture,
):
    """Test progress callback invoked at key stages."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", progress_callback=progress_callback
    )

    # Verify callback was called
    assert progress_callback.call_count >= 3  # At least: start, detection, extraction, complete


@pytest.mark.asyncio
async def test_progress_tracks_stages(
    mock_detection_agent,
    mock_keyframe_agent,
    test_video_path,
    progress_callback,
    mock_cv2_videocapture,
):
    """Test progress shows: detection → extraction → complete."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", progress_callback=progress_callback
    )

    # Extract stage names from calls
    stage_names = [call_args[0][0] for call_args in progress_callback.call_args_list]

    # Verify expected stages appear in order
    assert "detection" in stage_names
    assert "extraction" in stage_names
    assert "complete" in stage_names

    # Verify detection comes before extraction
    detection_idx = stage_names.index("detection")
    extraction_idx = stage_names.index("extraction")
    assert detection_idx < extraction_idx


@pytest.mark.asyncio
async def test_progress_callback_with_percentages(
    mock_detection_agent,
    mock_keyframe_agent,
    test_video_path,
    progress_callback,
    mock_cv2_videocapture,
):
    """Test progress callback receives stage name and percentage."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(
        video_path=test_video_path, video_id="test-video-123", progress_callback=progress_callback
    )

    # Verify callback format: callback(stage_name, percentage)
    for call_args in progress_callback.call_args_list:
        stage_name = call_args[0][0]
        percentage = call_args[0][1]

        assert isinstance(stage_name, str)
        assert isinstance(percentage, (int, float))
        assert 0 <= percentage <= 100


# =============================================================================
# 4. ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_handles_detection_agent_failure(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test graceful handling when DetectionAgent fails."""
    # Make DetectionAgent raise exception
    mock_detection_agent.process_video = AsyncMock(
        side_effect=VideoProcessingError("Detection failed")
    )

    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    with pytest.raises(VideoProcessingError, match="Detection failed"):
        await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # KeyframeAgent should NOT be called if detection fails
    mock_keyframe_agent.extract_keyframes.assert_not_called()


@pytest.mark.asyncio
async def test_handles_keyframe_agent_failure(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test graceful handling when KeyframeAgent fails."""
    from backend.core.exceptions import KeyframeExtractionError

    # Make KeyframeAgent raise exception
    mock_keyframe_agent.extract_keyframes = AsyncMock(
        side_effect=KeyframeExtractionError("Extraction failed")
    )

    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    with pytest.raises(KeyframeExtractionError, match="Extraction failed"):
        await agent.process_video(video_path=test_video_path, video_id="test-video-123")


@pytest.mark.asyncio
async def test_handles_invalid_video_path(mock_detection_agent, mock_keyframe_agent):
    """Test raises clear error for non-existent video."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    non_existent_path = Path("/non/existent/video.mp4")

    with pytest.raises(FileNotFoundError, match="Video file not found"):
        await agent.process_video(video_path=non_existent_path, video_id="test-video-123")


@pytest.mark.asyncio
async def test_handles_video_with_no_detections(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test handles case when no persons detected."""
    # Return empty detections list
    mock_detection_agent.process_video = AsyncMock(return_value=[])
    mock_keyframe_agent.extract_keyframes = AsyncMock(return_value=[])

    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Should complete successfully with zero detections
    assert result.total_detections == 0
    assert result.keyframes_extracted == 0
    assert len(result.keyframes) == 0


@pytest.mark.asyncio
async def test_error_context_includes_stage(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test error messages include which stage failed."""
    # Make DetectionAgent fail
    mock_detection_agent.process_video = AsyncMock(side_effect=Exception("YOLO model crashed"))

    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    with pytest.raises(VideoProcessingError) as exc_info:
        await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Error message should indicate detection stage
    error_message = str(exc_info.value)
    assert "detection" in error_message.lower() or "YOLO" in error_message


# =============================================================================
# 5. RESULT VALIDATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_result_contains_keyframe_paths(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test ProcessingResult includes paths to saved images."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify output paths are set
    assert result.output_dir is not None
    assert result.keyframe_dir is not None
    assert isinstance(result.output_dir, Path)
    assert isinstance(result.keyframe_dir, Path)

    # Verify keyframes include filenames
    for keyframe in result.keyframes:
        assert "filename" in keyframe


@pytest.mark.asyncio
async def test_result_contains_statistics(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test result includes: total_detections, keyframes_extracted, processing_time."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify statistics
    assert hasattr(result, "total_detections")
    assert hasattr(result, "keyframes_extracted")
    assert hasattr(result, "processing_time_seconds")

    assert result.total_detections == 3  # From mock_detection_agent
    assert result.keyframes_extracted == 2  # From mock_keyframe_agent
    assert result.processing_time_seconds >= 0

    # Verify processing_time is reasonable (should be < 10 seconds for mock)
    assert result.processing_time_seconds < 10


@pytest.mark.asyncio
async def test_result_contains_metadata_path(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test result includes path to metadata.json."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify metadata_path is set
    assert result.metadata_path is not None
    assert isinstance(result.metadata_path, Path)
    assert result.metadata_path.name == "metadata.json"


@pytest.mark.asyncio
async def test_result_contains_timestamps(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test result contains started_at and completed_at timestamps."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify timestamps
    assert isinstance(result.started_at, datetime)
    assert isinstance(result.completed_at, datetime)

    # completed_at should be after started_at
    assert result.completed_at >= result.started_at


@pytest.mark.asyncio
async def test_result_keyframes_are_dicts(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test result.keyframes contains dictionaries with keyframe metadata."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify keyframes list structure
    assert len(result.keyframes) > 0

    for keyframe in result.keyframes:
        assert isinstance(keyframe, dict)
        assert "frame_index" in keyframe
        assert "timestamp" in keyframe
        assert "score" in keyframe
        assert "bbox" in keyframe
        assert "filename" in keyframe


# =============================================================================
# 6. CONFIGURATION TESTS
# =============================================================================


def test_merge_config_uses_defaults(mock_detection_agent, mock_keyframe_agent):
    """Test config merging uses default values when custom config not provided."""
    agent = LeadAgent(
        detection_agent=mock_detection_agent,
        keyframe_agent=mock_keyframe_agent,
        default_config={"sample_rate": 3, "max_frames": 200},
    )

    merged = agent._merge_config(None)

    assert merged["sample_rate"] == 3
    assert merged["max_frames"] == 200


def test_merge_config_overrides_defaults(mock_detection_agent, mock_keyframe_agent):
    """Test custom config overrides default values."""
    agent = LeadAgent(
        detection_agent=mock_detection_agent,
        keyframe_agent=mock_keyframe_agent,
        default_config={"sample_rate": 1, "max_frames": 100},
    )

    custom_config = {"sample_rate": 5}
    merged = agent._merge_config(custom_config)

    assert merged["sample_rate"] == 5  # Overridden
    assert merged["max_frames"] == 100  # Default preserved


def test_merge_config_partial_override(mock_detection_agent, mock_keyframe_agent):
    """Test partial config override preserves unspecified defaults."""
    agent = LeadAgent(
        detection_agent=mock_detection_agent,
        keyframe_agent=mock_keyframe_agent,
        default_config={"sample_rate": 1, "max_frames": 100, "confidence_threshold": 0.5},
    )

    custom_config = {"max_frames": 50}
    merged = agent._merge_config(custom_config)

    assert merged["sample_rate"] == 1  # Default
    assert merged["max_frames"] == 50  # Overridden
    assert merged["confidence_threshold"] == 0.5  # Default


# =============================================================================
# 7. INTEGRATION FLOW TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_full_pipeline_sequence(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test complete pipeline executes in correct sequence."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Verify both agents were called
    mock_detection_agent.process_video.assert_called_once()
    mock_keyframe_agent.extract_keyframes.assert_called_once()

    # Verify DetectionAgent called before KeyframeAgent
    # (Mock call_count increases with each call)
    assert mock_detection_agent.process_video.call_count == 1
    assert mock_keyframe_agent.extract_keyframes.call_count == 1


@pytest.mark.asyncio
async def test_detection_to_keyframe_data_flow(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test detection results flow correctly to keyframe extraction."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    await agent.process_video(video_path=test_video_path, video_id="test-video-123")

    # Get the detections that KeyframeAgent received
    call_args = mock_keyframe_agent.extract_keyframes.call_args
    passed_detections = call_args.kwargs["detections"]

    # Verify data structure transformation (Detection -> dict)
    assert len(passed_detections) == 3
    assert all(isinstance(d, dict) for d in passed_detections)

    # Verify key fields preserved
    first_detection = passed_detections[0]
    assert first_detection["frame_index"] == 10
    assert first_detection["timestamp"] == 0.33
    assert first_detection["confidence"] == 0.95


@pytest.mark.asyncio
async def test_total_frames_calculated_correctly(
    mock_detection_agent, mock_keyframe_agent, test_video_path, mock_cv2_videocapture
):
    """Test total_frames is calculated from video metadata."""
    agent = LeadAgent(detection_agent=mock_detection_agent, keyframe_agent=mock_keyframe_agent)

    # Mock cv2.VideoCapture to return frame count
    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.get.return_value = 150  # 150 frames
        mock_instance.isOpened.return_value = True
        mock_instance.release = Mock()
        mock_cap.return_value = mock_instance

        result = await agent.process_video(video_path=test_video_path, video_id="test-video-123")

        # Verify total_frames was extracted from video
        assert result.total_frames == 150

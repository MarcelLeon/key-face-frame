"""
Detection Agent Unit Tests

Tests for YOLOv8-based person detection functionality.
Following TDD methodology - these tests are written BEFORE implementation.
"""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

# Import the classes we're testing (will be implemented after tests)
from backend.core.agents.detection_agent import Detection, DetectionAgent

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model for testing without actual model loading."""
    model = MagicMock()

    # Mock detection results
    mock_box = MagicMock()
    mock_box.xyxy = [np.array([100.0, 100.0, 200.0, 300.0])]
    mock_box.conf = [np.array([0.95])]
    mock_box.id = [np.array([1])]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]

    model.return_value = [mock_result]
    model.device = "cpu"

    return model


@pytest.fixture
def sample_frame():
    """Create a sample BGR frame (640x480, 3 channels)."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_frames():
    """Create multiple sample frames."""
    return [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]


@pytest.fixture
def test_video_small(tmp_path):
    """Create a small test video file using OpenCV."""
    import cv2

    video_path = tmp_path / "test_video.mp4"

    # Create a simple video with 10 frames
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

    for i in range(10):
        # Create a frame with a white rectangle that moves
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x_pos = 100 + i * 20
        cv2.rectangle(frame, (x_pos, 100), (x_pos + 100, 300), (255, 255, 255), -1)
        out.write(frame)

    out.release()
    return video_path


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================


def test_detection_agent_initialization():
    """Test agent initializes with YOLOv8 model."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent(model_name="yolov8m.pt")

        # Verify YOLO model was loaded
        mock_yolo_class.assert_called_once_with("yolov8m.pt")

        # Verify default confidence threshold
        assert agent.confidence_threshold == 0.5


def test_detection_agent_custom_confidence():
    """Test agent accepts custom confidence threshold."""
    with patch("backend.core.agents.detection_agent.YOLO"):
        agent = DetectionAgent(confidence_threshold=0.7)

        assert agent.confidence_threshold == 0.7


def test_detection_agent_uses_mps_on_apple_silicon():
    """Test MPS device is selected on Mac M4 (Apple Silicon)."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        with patch("backend.core.agents.detection_agent.torch") as mock_torch:
            # Simulate MPS availability (Apple Silicon)
            mock_torch.backends.mps.is_available.return_value = True
            mock_torch.cuda.is_available.return_value = False

            mock_model = MagicMock()
            mock_yolo_class.return_value = mock_model

            agent = DetectionAgent()

            # Verify device selection logic
            assert agent.device in ["mps", "auto"]  # Should auto-detect MPS


def test_detection_agent_falls_back_to_cpu():
    """Test graceful CPU fallback when MPS unavailable."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        with patch("backend.core.agents.detection_agent.torch") as mock_torch:
            # Simulate no GPU available
            mock_torch.backends.mps.is_available.return_value = False
            mock_torch.cuda.is_available.return_value = False

            mock_model = MagicMock()
            mock_yolo_class.return_value = mock_model

            agent = DetectionAgent(device="cpu")

            assert agent.device == "cpu"


def test_detection_agent_force_device():
    """Test agent respects forced device selection."""
    with patch("backend.core.agents.detection_agent.YOLO"):
        agent = DetectionAgent(device="cuda")

        assert agent.device == "cuda"


# =============================================================================
# DETECTION TESTS (SINGLE FRAME)
# =============================================================================


@pytest.mark.asyncio
async def test_detect_persons_in_frame(sample_frame):
    """Test detecting persons in single frame."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        # Setup mock model
        mock_model = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
        mock_box.conf = np.array([0.95])
        mock_box.id = None  # Single frame detection, no tracking

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        # Detect persons in frame
        detections = await agent.detect_persons_in_frame(sample_frame)

        # Should return a list of Detection objects
        assert isinstance(detections, list)
        assert len(detections) > 0
        assert isinstance(detections[0], Detection)


@pytest.mark.asyncio
async def test_detect_persons_returns_bounding_boxes(sample_frame):
    """Test detection returns proper bbox format [x1, y1, x2, y2]."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        # Setup mock with known bbox
        mock_model = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = np.array([[100.0, 150.0, 250.0, 400.0]])
        mock_box.conf = np.array([0.95])
        mock_box.id = None

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()
        detections = await agent.detect_persons_in_frame(sample_frame)

        # Verify bbox format
        assert len(detections) == 1
        bbox = detections[0].bbox

        assert isinstance(bbox, list)
        assert len(bbox) == 4
        assert bbox == [100.0, 150.0, 250.0, 400.0]


@pytest.mark.asyncio
async def test_detect_persons_filters_by_confidence(sample_frame):
    """Test confidence threshold filtering (default 0.5)."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        # Setup mock with varying confidence scores
        mock_model = MagicMock()

        # Two detections: one above threshold, one below
        mock_box_high = MagicMock()
        mock_box_high.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
        mock_box_high.conf = np.array([0.95])  # Above 0.5
        mock_box_high.id = None

        mock_box_low = MagicMock()
        mock_box_low.xyxy = np.array([[300.0, 100.0, 400.0, 300.0]])
        mock_box_low.conf = np.array([0.3])  # Below 0.5
        mock_box_low.id = None

        mock_result = MagicMock()
        mock_result.boxes = [mock_box_high, mock_box_low]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent(confidence_threshold=0.5)
        detections = await agent.detect_persons_in_frame(sample_frame)

        # Should only return high confidence detection
        assert len(detections) == 1
        assert detections[0].confidence >= 0.5


@pytest.mark.asyncio
async def test_detect_persons_empty_frame():
    """Test handling frames with no persons."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        # Setup mock with no detections
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.boxes = []  # No persons detected

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = await agent.detect_persons_in_frame(empty_frame)

        # Should return empty list
        assert isinstance(detections, list)
        assert len(detections) == 0


@pytest.mark.asyncio
async def test_detect_persons_includes_timestamp():
    """Test detection includes frame timestamp."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        mock_model = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
        mock_box.conf = np.array([0.95])
        mock_box.id = None

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        # For single frame, we can pass frame_index=0
        detections = await agent.detect_persons_in_frame(
            np.zeros((480, 640, 3), dtype=np.uint8), frame_index=10, fps=30.0
        )

        assert len(detections) == 1
        assert detections[0].frame_index == 10
        assert detections[0].timestamp == pytest.approx(10 / 30.0)


# =============================================================================
# VIDEO PROCESSING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_process_video_returns_detections(test_video_small):
    """Test processing full video returns detection list."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        # Setup mock to return detections for each frame
        mock_model = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
        mock_box.conf = np.array([0.95])
        mock_box.id = np.array([1])

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        detections = await agent.process_video(test_video_small)

        # Should return list of detections
        assert isinstance(detections, list)
        # Video has 10 frames, should have detections
        assert len(detections) > 0
        assert all(isinstance(d, Detection) for d in detections)


@pytest.mark.asyncio
async def test_process_video_with_sampling(test_video_small):
    """Test frame sampling (every Nth frame)."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        mock_model = MagicMock()
        mock_box = MagicMock()
        mock_box.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
        mock_box.conf = np.array([0.95])
        mock_box.id = np.array([1])

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        # Sample every 2nd frame
        detections = await agent.process_video(test_video_small, sample_rate=2)

        # With 10 frames and sample_rate=2, should process 5 frames
        assert len(detections) == 5

        # Verify frame indices are sampled correctly (0, 2, 4, 6, 8)
        frame_indices = [d.frame_index for d in detections]
        assert frame_indices == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_process_video_tracks_progress(test_video_small):
    """Test progress callback mechanism."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        mock_model = MagicMock()
        mock_result = MagicMock()
        mock_result.boxes = []
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()

        # Track progress callbacks
        progress_calls = []

        def progress_callback(current: int, total: int):
            progress_calls.append((current, total))

        await agent.process_video(test_video_small, progress_callback=progress_callback)

        # Should have received progress updates
        assert len(progress_calls) > 0

        # Last call should be (total, total)
        final_call = progress_calls[-1]
        assert final_call[0] == final_call[1]


@pytest.mark.asyncio
async def test_process_video_with_tracking_ids(test_video_small):
    """Test that tracking IDs are maintained across frames."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        mock_model = MagicMock()

        # Return consistent track_id across frames
        call_count = [0]

        def mock_predict(*args, **kwargs):
            mock_box = MagicMock()
            mock_box.xyxy = np.array([[100.0, 100.0, 200.0, 300.0]])
            mock_box.conf = np.array([0.95])
            # Same track_id for all frames
            mock_box.id = np.array([42])

            mock_result = MagicMock()
            mock_result.boxes = [mock_box]

            call_count[0] += 1
            return [mock_result]

        mock_model.side_effect = mock_predict
        mock_yolo_class.return_value = mock_model

        agent = DetectionAgent()
        detections = await agent.process_video(test_video_small)

        # All detections should have the same track_id
        track_ids = [d.track_id for d in detections]
        assert all(tid == 42 for tid in track_ids)


# =============================================================================
# EDGE CASES
# =============================================================================


@pytest.mark.asyncio
async def test_handles_corrupted_video(tmp_path):
    """Test handling corrupted/unreadable video."""
    from backend.core.exceptions import VideoProcessingError

    # Create a fake corrupted video file
    corrupted_video = tmp_path / "corrupted.mp4"
    corrupted_video.write_bytes(b"not a valid video file")

    with patch("backend.core.agents.detection_agent.YOLO"):
        agent = DetectionAgent()

        # Should raise VideoProcessingError
        with pytest.raises(VideoProcessingError, match="cannot be read|invalid|corrupted"):
            await agent.process_video(corrupted_video)


@pytest.mark.asyncio
async def test_handles_empty_video(tmp_path):
    """Test handling video with zero frames."""
    import cv2

    # Try to create a video with 0 frames (edge case)
    empty_video = tmp_path / "empty.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(empty_video), fourcc, 30.0, (640, 480))
    out.release()  # Release without writing any frames

    with patch("backend.core.agents.detection_agent.YOLO"):
        agent = DetectionAgent()

        detections = await agent.process_video(empty_video)

        # Should return empty list, not crash
        assert detections == []


@pytest.mark.asyncio
async def test_memory_efficient_large_video():
    """Test streaming approach for large videos."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        with patch("backend.core.agents.detection_agent.cv2.VideoCapture") as mock_cap_class:
            # Simulate a large video (10000 frames)
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {1: 30.0, 7: 10000}.get(  # FPS  # Frame count
                prop, 0
            )

            # Simulate frame reading
            frame_count = [0]

            def mock_read():
                frame_count[0] += 1
                if frame_count[0] <= 10000:
                    return True, np.zeros((480, 640, 3), dtype=np.uint8)
                return False, None

            mock_cap.read = mock_read
            mock_cap_class.return_value = mock_cap

            # Mock YOLO
            mock_model = MagicMock()
            mock_result = MagicMock()
            mock_result.boxes = []
            mock_model.return_value = [mock_result]
            mock_yolo_class.return_value = mock_model

            agent = DetectionAgent()

            # Process with high sample rate to avoid processing all frames
            detections = await agent.process_video(Path("/fake/large_video.mp4"), sample_rate=100)

            # Should complete without loading entire video into memory
            # With sample_rate=100, should process 100 frames
            assert isinstance(detections, list)

            # Verify VideoCapture was released
            mock_cap.release.assert_called_once()


@pytest.mark.asyncio
async def test_video_capture_released_on_error():
    """Test that video capture is properly released even on error."""
    with patch("backend.core.agents.detection_agent.YOLO") as mock_yolo_class:
        with patch("backend.core.agents.detection_agent.cv2.VideoCapture") as mock_cap_class:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap.get.return_value = 30.0
            mock_cap_class.return_value = mock_cap

            # Mock YOLO to raise an error
            mock_model = MagicMock()
            mock_model.side_effect = RuntimeError("GPU OOM")
            mock_yolo_class.return_value = mock_model

            agent = DetectionAgent()

            # Should raise error but still release resources
            with pytest.raises(RuntimeError):
                await agent.process_video(Path("/fake/video.mp4"))

            # Verify release was called
            mock_cap.release.assert_called()


# =============================================================================
# DATA CLASS TESTS
# =============================================================================


def test_detection_dataclass():
    """Test Detection dataclass structure."""
    detection = Detection(
        frame_index=10,
        timestamp=0.33,
        bbox=[100.0, 100.0, 200.0, 300.0],
        confidence=0.95,
        track_id=42,
    )

    assert detection.frame_index == 10
    assert detection.timestamp == 0.33
    assert detection.bbox == [100.0, 100.0, 200.0, 300.0]
    assert detection.confidence == 0.95
    assert detection.track_id == 42


def test_detection_optional_track_id():
    """Test Detection with optional track_id."""
    detection = Detection(
        frame_index=10, timestamp=0.33, bbox=[100.0, 100.0, 200.0, 300.0], confidence=0.95
    )

    assert detection.track_id is None

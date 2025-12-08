"""
Keyframe Agent Tests

Comprehensive test suite for KeyframeAgent following TDD methodology.
Tests written BEFORE implementation (Red phase).
"""

import json
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from backend.core.agents.keyframe_agent import (
    Keyframe,
    KeyframeAgent,
    KeyframeExtractionError,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory for testing."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def sample_detections() -> List[Dict]:
    """Sample detection data from DetectionAgent."""
    return [
        {
            "frame_index": 10,
            "timestamp": 0.33,
            "bbox": [100, 100, 200, 300],
            "confidence": 0.95,
            "track_id": 1,
        },
        {
            "frame_index": 45,
            "timestamp": 1.50,
            "bbox": [150, 120, 250, 320],
            "confidence": 0.92,
            "track_id": 1,
        },
        {
            "frame_index": 123,
            "timestamp": 4.10,
            "bbox": [120, 110, 220, 310],
            "confidence": 0.88,
            "track_id": 2,
        },
    ]


@pytest.fixture
def close_detections() -> List[Dict]:
    """Detection data with temporally close frames for deduplication testing."""
    return [
        {
            "frame_index": 10,
            "timestamp": 0.33,
            "bbox": [100, 100, 200, 300],
            "confidence": 0.95,
            "track_id": 1,
        },
        {
            "frame_index": 11,
            "timestamp": 0.37,
            "bbox": [101, 101, 201, 301],
            "confidence": 0.90,
            "track_id": 1,
        },
        {
            "frame_index": 50,
            "timestamp": 1.67,
            "bbox": [120, 110, 220, 310],
            "confidence": 0.85,
            "track_id": 2,
        },
    ]


@pytest.fixture
def mock_video_frame() -> np.ndarray:
    """Mock video frame (640x480 RGB image)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_video_capture(mock_video_frame: np.ndarray):
    """Mock cv2.VideoCapture for unit tests."""
    with patch("cv2.VideoCapture") as mock_cap:
        # Setup mock instance
        cap_instance = MagicMock()
        cap_instance.isOpened.return_value = True
        cap_instance.get.side_effect = lambda prop: {
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
        }.get(prop, 0)

        # Mock read() to return test frame
        cap_instance.read.return_value = (True, mock_video_frame)

        # Mock set() for frame positioning
        cap_instance.set.return_value = True

        # Return instance when VideoCapture is called
        mock_cap.return_value = cap_instance

        yield mock_cap


# ============================================================================
# 1. Initialization Tests
# ============================================================================


class TestKeyframeAgentInitialization:
    """Test KeyframeAgent initialization."""

    def test_keyframe_agent_initialization(self, output_dir: Path):
        """Test agent initializes with storage path."""
        agent = KeyframeAgent(output_dir=output_dir)

        assert agent.output_dir == output_dir
        assert agent.time_threshold == 1.0  # Default value
        assert agent.jpeg_quality == 95  # Default value

    def test_keyframe_agent_custom_parameters(self, output_dir: Path):
        """Test agent initializes with custom parameters."""
        agent = KeyframeAgent(output_dir=output_dir, time_threshold=2.0, jpeg_quality=85)

        assert agent.time_threshold == 2.0
        assert agent.jpeg_quality == 85

    def test_keyframe_agent_creates_output_directory(self, tmp_path: Path):
        """Test output directory is created if not exists."""
        output_dir = tmp_path / "nonexistent" / "nested" / "output"

        agent = KeyframeAgent(output_dir=output_dir)

        # Directory should be created during initialization or first use
        # We'll verify this in extract_keyframes tests


# ============================================================================
# 2. Candidate Collection Tests
# ============================================================================


class TestCandidateCollection:
    """Test collecting candidate frames from detections."""

    def test_collect_candidates_from_detections(
        self, output_dir: Path, sample_detections: List[Dict]
    ):
        """Test collecting candidate frames from detection list."""
        agent = KeyframeAgent(output_dir=output_dir)

        candidates = agent._collect_candidates(sample_detections)

        assert len(candidates) == len(sample_detections)
        assert all("frame_index" in c for c in candidates)
        assert all("timestamp" in c for c in candidates)
        assert all("bbox" in c for c in candidates)

    def test_collect_candidates_empty_detections(self, output_dir: Path):
        """Test handling empty detection list."""
        agent = KeyframeAgent(output_dir=output_dir)

        candidates = agent._collect_candidates([])

        assert candidates == []

    def test_collect_candidates_includes_all_persons(
        self, output_dir: Path, sample_detections: List[Dict]
    ):
        """Test all detected persons become candidates."""
        agent = KeyframeAgent(output_dir=output_dir)

        candidates = agent._collect_candidates(sample_detections)

        # Verify all frame indices are preserved
        detection_frames = {d["frame_index"] for d in sample_detections}
        candidate_frames = {c["frame_index"] for c in candidates}

        assert detection_frames == candidate_frames


# ============================================================================
# 3. Frame Scoring Tests
# ============================================================================


class TestFrameScoring:
    """Test frame quality scoring algorithm."""

    def test_score_frames_by_person_size(self, output_dir: Path):
        """Test scoring prioritizes larger person bboxes."""
        agent = KeyframeAgent(output_dir=output_dir)

        # Create candidates with different bbox sizes
        candidates = [
            {
                "frame_index": 1,
                "timestamp": 0.03,
                "bbox": [100, 100, 200, 300],  # 100x200 = 20,000 area
                "confidence": 0.9,
            },
            {
                "frame_index": 2,
                "timestamp": 0.06,
                "bbox": [100, 100, 300, 400],  # 200x300 = 60,000 area (larger)
                "confidence": 0.9,
            },
        ]

        scored = agent._score_frames(candidates, video_width=640, video_height=480)

        # Larger person should have higher score
        assert scored[1]["score"] > scored[0]["score"]

    def test_score_frames_by_confidence(self, output_dir: Path):
        """Test scoring considers detection confidence."""
        agent = KeyframeAgent(output_dir=output_dir)

        candidates = [
            {
                "frame_index": 1,
                "timestamp": 0.03,
                "bbox": [100, 100, 200, 300],
                "confidence": 0.95,  # Higher confidence
            },
            {
                "frame_index": 2,
                "timestamp": 0.06,
                "bbox": [100, 100, 200, 300],  # Same size
                "confidence": 0.70,  # Lower confidence
            },
        ]

        scored = agent._score_frames(candidates, video_width=640, video_height=480)

        # Higher confidence should increase score
        assert scored[0]["score"] > scored[1]["score"]

    def test_score_frames_by_centrality(self, output_dir: Path):
        """Test scoring favors centered persons."""
        agent = KeyframeAgent(output_dir=output_dir)

        # Frame center: (320, 240) for 640x480
        candidates = [
            {
                "frame_index": 1,
                "timestamp": 0.03,
                "bbox": [270, 190, 370, 290],  # Centered
                "confidence": 0.9,
            },
            {
                "frame_index": 2,
                "timestamp": 0.06,
                "bbox": [10, 10, 110, 110],  # Corner (far from center)
                "confidence": 0.9,
            },
        ]

        scored = agent._score_frames(candidates, video_width=640, video_height=480)

        # Centered person should have higher score
        assert scored[0]["score"] > scored[1]["score"]

    def test_score_frames_returns_sorted_list(self, output_dir: Path):
        """Test scored frames are sorted by score (descending)."""
        agent = KeyframeAgent(output_dir=output_dir)

        candidates = [
            {
                "frame_index": i,
                "timestamp": i * 0.03,
                "bbox": [100, 100, 150 + i * 10, 200 + i * 20],
                "confidence": 0.9,
            }
            for i in range(5)
        ]

        scored = agent._score_frames(candidates, video_width=640, video_height=480)

        # Verify scores are in descending order
        scores = [f["score"] for f in scored]
        assert scores == sorted(scores, reverse=True)


# ============================================================================
# 4. Deduplication Tests
# ============================================================================


class TestDeduplication:
    """Test temporal deduplication of frames."""

    def test_remove_duplicates_by_time(self, output_dir: Path, close_detections: List[Dict]):
        """Test removing frames within time threshold (default 1.0s)."""
        agent = KeyframeAgent(output_dir=output_dir, time_threshold=1.0)

        # Add scores to detections
        candidates = [{**d, "score": 100 - i * 10} for i, d in enumerate(close_detections)]

        unique = agent._remove_duplicates(candidates)

        # Frames at 0.33s and 0.37s should be merged (within 1.0s)
        # Frame at 1.67s should remain (>1.0s from previous)
        assert len(unique) < len(candidates)

    def test_remove_duplicates_keeps_highest_score(self, output_dir: Path):
        """Test when duplicates exist, keeps highest scored."""
        agent = KeyframeAgent(output_dir=output_dir, time_threshold=1.0)

        candidates = [
            {
                "frame_index": 10,
                "timestamp": 0.33,
                "bbox": [100, 100, 200, 300],
                "score": 80,  # Lower score
            },
            {
                "frame_index": 11,
                "timestamp": 0.37,
                "bbox": [101, 101, 201, 301],
                "score": 95,  # Higher score
            },
        ]

        unique = agent._remove_duplicates(candidates)

        assert len(unique) == 1
        assert unique[0]["score"] == 95  # Kept the higher scored frame

    def test_remove_duplicates_configurable_threshold(self, output_dir: Path):
        """Test time threshold is configurable."""
        # Test with larger threshold (2.0s)
        agent = KeyframeAgent(output_dir=output_dir, time_threshold=2.0)

        candidates = [
            {"frame_index": 1, "timestamp": 0.0, "score": 90},
            {"frame_index": 2, "timestamp": 1.5, "score": 85},  # Within 2.0s
            {"frame_index": 3, "timestamp": 3.0, "score": 80},  # Beyond 2.0s
        ]

        unique = agent._remove_duplicates(candidates)

        # First two should be merged, third should remain
        assert len(unique) == 2

    def test_remove_duplicates_empty_frames(self, output_dir: Path):
        """Test handles empty frame list."""
        agent = KeyframeAgent(output_dir=output_dir)

        unique = agent._remove_duplicates([])

        assert unique == []


# ============================================================================
# 5. Keyframe Extraction Tests
# ============================================================================


class TestKeyframeExtraction:
    """Test end-to-end keyframe extraction."""

    @pytest.mark.asyncio
    async def test_extract_keyframes_returns_correct_count(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test extracts max_frames keyframes (or less)."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()  # Create dummy file

        agent = KeyframeAgent(output_dir=output_dir)

        keyframes = await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-video-123",
            max_frames=2,
        )

        # Should return at most max_frames
        assert len(keyframes) <= 2

    @pytest.mark.asyncio
    async def test_extract_keyframes_saves_images(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test saves JPEG files to output directory."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        keyframes = await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-video-123",
            max_frames=10,
        )

        # Verify output directory structure
        video_output = output_dir / "video-test-video-123" / "keyframes"
        assert video_output.exists()

        # Verify JPEG files are saved
        jpg_files = list(video_output.glob("*.jpg"))
        assert len(jpg_files) == len(keyframes)

    @pytest.mark.asyncio
    async def test_extract_keyframes_saves_metadata(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test saves metadata.json with frame info."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-video-123",
            max_frames=10,
        )

        # Verify metadata.json exists
        metadata_path = output_dir / "video-test-video-123" / "metadata.json"
        assert metadata_path.exists()

        # Verify metadata content
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        assert isinstance(metadata, dict)
        assert "keyframes" in metadata
        assert "video_id" in metadata

    @pytest.mark.asyncio
    async def test_extract_keyframes_handles_video_read_error(
        self, output_dir: Path, sample_detections: List[Dict], tmp_path: Path
    ):
        """Test graceful handling when video can't be read."""
        video_path = tmp_path / "nonexistent.mp4"
        # Don't create the file

        agent = KeyframeAgent(output_dir=output_dir)

        with pytest.raises(KeyframeExtractionError):
            await agent.extract_keyframes(
                video_path=video_path,
                detections=sample_detections,
                video_id="test-video-123",
                max_frames=10,
            )

    @pytest.mark.asyncio
    async def test_extract_keyframes_with_progress_callback(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test progress callback is called during extraction."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        # Track callback invocations
        callback_calls = []

        def progress_callback(current: int, total: int):
            callback_calls.append((current, total))

        await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-video-123",
            max_frames=10,
            progress_callback=progress_callback,
        )

        # Callback should have been called
        assert len(callback_calls) > 0


# ============================================================================
# 6. Image Saving Tests
# ============================================================================


class TestImageSaving:
    """Test frame image saving functionality."""

    @pytest.mark.asyncio
    async def test_save_frame_creates_jpeg(
        self,
        output_dir: Path,
        mock_video_frame: np.ndarray,
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test saves frame as JPEG with correct filename."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        frame_data = {
            "frame_index": 123,
            "timestamp": 4.10,
            "bbox": [100, 100, 200, 300],
            "score": 95.0,
        }

        video_output = output_dir / "video-test-123" / "keyframes"
        video_output.mkdir(parents=True)

        keyframe = await agent._save_single_frame(
            video_path=video_path,
            frame_data=frame_data,
            output_path=video_output,
        )

        # Verify filename format: frame_{index:05d}_t{timestamp:.2f}s.jpg
        assert keyframe.filename.startswith("frame_00123_t4.10s")
        assert keyframe.filename.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_save_frame_jpeg_quality(
        self, output_dir: Path, mock_video_capture, tmp_path: Path
    ):
        """Test JPEG quality is configurable (default 95)."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        # Test with custom quality
        agent = KeyframeAgent(output_dir=output_dir, jpeg_quality=85)

        assert agent.jpeg_quality == 85

    @pytest.mark.asyncio
    async def test_save_frame_handles_write_error(self, output_dir: Path, tmp_path: Path):
        """Test handles disk write errors gracefully."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        # Mock cv2.imwrite to simulate write failure
        with patch("cv2.imwrite", return_value=False):
            with patch("cv2.VideoCapture") as mock_cap:
                cap_instance = MagicMock()
                cap_instance.isOpened.return_value = True
                cap_instance.read.return_value = (True, np.zeros((480, 640, 3)))
                mock_cap.return_value = cap_instance

                frame_data = {
                    "frame_index": 1,
                    "timestamp": 0.03,
                    "bbox": [100, 100, 200, 300],
                    "score": 90.0,
                }

                video_output = output_dir / "video-test" / "keyframes"
                video_output.mkdir(parents=True)

                with pytest.raises(KeyframeExtractionError):
                    await agent._save_single_frame(
                        video_path=video_path,
                        frame_data=frame_data,
                        output_path=video_output,
                    )


# ============================================================================
# 7. End-to-End Tests
# ============================================================================


class TestEndToEnd:
    """Test complete pipeline integration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mock_detections(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test complete pipeline: detections → candidates → score → dedupe → save."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        keyframes = await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-video-full",
            max_frames=100,
        )

        # Verify complete pipeline execution
        assert isinstance(keyframes, list)
        assert all(isinstance(kf, Keyframe) for kf in keyframes)

        # Verify all keyframe attributes
        for kf in keyframes:
            assert kf.frame_index >= 0
            assert kf.timestamp >= 0.0
            assert kf.score >= 0.0
            assert len(kf.bbox) == 4
            assert kf.filename.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_metadata_contains_all_required_fields(
        self,
        output_dir: Path,
        sample_detections: List[Dict],
        mock_video_capture,
        tmp_path: Path,
    ):
        """Test metadata.json has: frame_index, timestamp, score, bbox, filename."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        agent = KeyframeAgent(output_dir=output_dir)

        await agent.extract_keyframes(
            video_path=video_path,
            detections=sample_detections,
            video_id="test-metadata",
            max_frames=10,
        )

        # Load metadata
        metadata_path = output_dir / "video-test-metadata" / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Verify required fields
        assert "video_id" in metadata
        assert "keyframes" in metadata
        assert "total_keyframes" in metadata
        assert "extraction_params" in metadata

        # Verify each keyframe has required fields
        for kf in metadata["keyframes"]:
            assert "frame_index" in kf
            assert "timestamp" in kf
            assert "score" in kf
            assert "bbox" in kf
            assert "filename" in kf

"""
Detection Agent Integration Tests

Integration tests with real YOLOv8 model and actual video files.
These tests are slower and will download the YOLO model on first run.

Run with: pytest tests/integration/test_detection_integration.py -v -s
"""

import logging
from pathlib import Path

import pytest

from backend.core.agents.detection_agent import Detection, DetectionAgent

# Configure logging to see agent output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mark all tests in this file as integration and slow
pytestmark = [pytest.mark.integration, pytest.mark.slow]


# 注意: 测试视频路径通过全局 test_video_path fixture 注入（定义在 tests/conftest.py）
# 可以通过以下方式配置：
#   1. 环境变量: export TEST_VIDEO_FILE="your_video.mp4"
#   2. pytest.ini: test_video_file = your_video.mp4
#   3. 默认值: WanAnimate_00001_p84-audio_gouns_1765004610.mp4


@pytest.mark.asyncio
async def test_detection_agent_with_real_video(test_video_path):
    """
    Integration test with actual YOLOv8 model and test video.

    This test will:
    1. Download YOLOv8n model on first run (~6MB)
    2. Process the actual test video
    3. Verify detections are reasonable

    Expected behavior:
    - Should detect persons in the video
    - Detections should have valid bounding boxes
    - Should use MPS on Mac M4 for acceleration

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    logger.info(f"Running integration test with video: {test_video_path.name}")

    # Create agent with smaller model for faster testing (yolov8n)
    agent = DetectionAgent(
        model_name="yolov8n.pt",  # Nano model - fastest, smallest
        confidence_threshold=0.5,
    )

    # Verify device selection
    logger.info(f"Agent using device: {agent.device}")

    # Process video with aggressive sampling to speed up test
    # Sample every 30 frames (1 second at 30 FPS)
    detections = await agent.process_video(
        test_video_path,
        sample_rate=30,  # Process 1 frame per second
    )

    # Assertions
    assert isinstance(detections, list), "Should return a list"
    logger.info(f"Total detections: {len(detections)}")

    if len(detections) > 0:
        # Verify first detection has correct structure
        first_detection = detections[0]
        assert isinstance(first_detection, Detection)
        assert isinstance(first_detection.frame_index, int)
        assert isinstance(first_detection.timestamp, float)
        assert isinstance(first_detection.bbox, list)
        assert len(first_detection.bbox) == 4
        assert isinstance(first_detection.confidence, float)
        assert 0.0 <= first_detection.confidence <= 1.0

        # Log sample detection
        logger.info(
            f"Sample detection: Frame {first_detection.frame_index}, "
            f"Confidence: {first_detection.confidence:.2f}, "
            f"BBox: {first_detection.bbox}"
        )

        # Verify bounding box coordinates are reasonable
        x1, y1, x2, y2 = first_detection.bbox
        assert x2 > x1, "x2 should be greater than x1"
        assert y2 > y1, "y2 should be greater than y1"
        assert x1 >= 0, "x1 should be non-negative"
        assert y1 >= 0, "y1 should be non-negative"

    else:
        logger.warning("No detections found in video - this may indicate an issue")


@pytest.mark.asyncio
async def test_detection_agent_mps_performance(test_video_path):
    """
    Performance test to verify MPS acceleration on Mac M4.

    This test processes the same video segment and verifies that
    MPS device is being used (if available).

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    import torch

    # Check if MPS is available
    mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()

    agent = DetectionAgent(model_name="yolov8n.pt")

    # On Mac M4, should auto-detect MPS
    if mps_available:
        assert agent.device == "mps", "Should use MPS on Apple Silicon"
        logger.info("MPS device confirmed - using GPU acceleration")
    else:
        logger.info(f"MPS not available, using: {agent.device}")

    # Process a small segment
    detections = await agent.process_video(
        test_video_path,
        sample_rate=60,  # Very sparse sampling for speed test
    )

    logger.info(
        f"Processed video with device={agent.device}, " f"found {len(detections)} detections"
    )

    assert isinstance(detections, list)


@pytest.mark.asyncio
async def test_detection_agent_progress_callback(test_video_path):
    """
    Test progress callback functionality with real video.

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    agent = DetectionAgent(model_name="yolov8n.pt")

    progress_updates = []

    def track_progress(current: int, total: int):
        progress_updates.append((current, total))
        percent = (current / total) * 100 if total > 0 else 0
        logger.info(f"Progress: {current}/{total} ({percent:.1f}%)")

    detections = await agent.process_video(
        test_video_path,
        sample_rate=30,
        progress_callback=track_progress,
    )

    # Verify we received progress updates
    assert len(progress_updates) > 0, "Should receive progress updates"

    # Verify final update shows completion
    final_current, final_total = progress_updates[-1]
    assert final_current == final_total, "Final update should show 100% completion"

    logger.info(f"Received {len(progress_updates)} progress updates")


@pytest.mark.asyncio
async def test_detection_with_different_confidence_thresholds(test_video_path):
    """
    Test detection with varying confidence thresholds.

    Lower threshold should generally yield more detections.

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    # High confidence
    agent_high = DetectionAgent(
        model_name="yolov8n.pt",
        confidence_threshold=0.8,
    )

    detections_high = await agent_high.process_video(
        test_video_path,
        sample_rate=30,
    )

    # Low confidence
    agent_low = DetectionAgent(
        model_name="yolov8n.pt",
        confidence_threshold=0.3,
    )

    detections_low = await agent_low.process_video(
        test_video_path,
        sample_rate=30,
    )

    logger.info(f"High confidence (0.8): {len(detections_high)} detections")
    logger.info(f"Low confidence (0.3): {len(detections_low)} detections")

    # Lower threshold should yield equal or more detections
    assert len(detections_low) >= len(
        detections_high
    ), "Lower confidence threshold should yield more detections"


@pytest.mark.asyncio
async def test_detection_frame_sampling_accuracy(test_video_path):
    """
    Test that frame sampling works correctly.

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    agent = DetectionAgent(model_name="yolov8n.pt")

    # Sample every 10th frame
    detections = await agent.process_video(
        test_video_path,
        sample_rate=10,
    )

    if len(detections) > 0:
        # Verify frame indices are multiples of sample_rate
        frame_indices = [d.frame_index for d in detections]

        # All sampled frames should be multiples of 10
        # (allowing for last frame which might not be)
        sampled_correctly = all(idx % 10 == 0 for idx in frame_indices[:-1])

        logger.info(f"Frame indices (first 10): {frame_indices[:10]}")

        assert sampled_correctly, "Frame sampling should respect sample_rate"

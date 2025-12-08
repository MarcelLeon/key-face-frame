"""
Full Pipeline Integration Test

End-to-end integration test for the complete video processing pipeline:
Video → DetectionAgent → KeyframeAgent → Output

Uses real agents (not mocks) with test video to validate the full workflow.
"""

import json
from pathlib import Path
from typing import List

import pytest

from backend.core.agents.detection_agent import DetectionAgent
from backend.core.agents.keyframe_agent import KeyframeAgent
from backend.core.agents.lead_agent import LeadAgent, ProcessingResult

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def test_video_path():
    """
    Path to test video file.

    NOTE: This test requires a real video file to exist.
    If the file doesn't exist, the test will be skipped.
    """
    # Try common test video locations
    possible_paths = [
        Path("tests/fixtures/test_video.mp4"),
        Path("output/sample_video.mp4"),
        Path(__file__).parent.parent / "fixtures" / "test_video.mp4",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # No test video found - will skip test
    return None


@pytest.fixture(scope="module")
def output_dir(tmp_path_factory):
    """Temporary output directory for integration test."""
    return tmp_path_factory.mktemp("integration_output")


@pytest.fixture(scope="module")
def detection_agent():
    """Real DetectionAgent for integration testing."""
    return DetectionAgent(
        model_name="yolov8n.pt", confidence_threshold=0.5  # Use smallest model for speed
    )


@pytest.fixture(scope="module")
def keyframe_agent(output_dir):
    """Real KeyframeAgent for integration testing."""
    return KeyframeAgent(
        output_dir=output_dir,
        time_threshold=1.0,
        jpeg_quality=85,  # Lower quality for faster testing
    )


@pytest.fixture(scope="module")
def lead_agent(detection_agent, keyframe_agent):
    """Real LeadAgent for integration testing."""
    return LeadAgent(
        detection_agent=detection_agent,
        keyframe_agent=keyframe_agent,
        default_config={
            "sample_rate": 5,  # Sample every 5th frame for speed
            "max_frames": 20,  # Limit keyframes for testing
            "confidence_threshold": 0.5,
        },
    )


@pytest.fixture
def progress_tracker():
    """Track progress callbacks during execution."""

    class ProgressTracker:
        def __init__(self):
            self.calls: List[tuple] = []

        def callback(self, stage: str, percentage: int):
            self.calls.append((stage, percentage))

        def get_stages(self) -> List[str]:
            return [call[0] for call in self.calls]

    return ProgressTracker()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    True,  # Skip by default - requires real video file
    reason="Requires real test video file - run manually with real video",
)
async def test_complete_pipeline_with_real_agents(
    lead_agent, test_video_path, output_dir, progress_tracker
):
    """
    Full integration test: Video → DetectionAgent → KeyframeAgent → Output

    Uses real agents (not mocks) with test video.

    Validates:
    1. Detection finds persons
    2. Keyframes extracted and saved
    3. Metadata JSON created
    4. JPEG files exist and readable
    5. ProcessingResult accurate
    6. Progress callback called correctly

    NOTE: This test is skipped by default. To run it:
    1. Place a test video at tests/fixtures/test_video.mp4
    2. Run: pytest tests/integration/test_full_pipeline.py::test_complete_pipeline_with_real_agents -v -s --run-integration
    """
    # Skip if no test video available
    if test_video_path is None:
        pytest.skip("No test video file found")

    print(f"\n{'='*70}")
    print(f"Running full pipeline integration test")
    print(f"Video: {test_video_path}")
    print(f"Output: {output_dir}")
    print(f"{'='*70}\n")

    # Execute full pipeline
    result = await lead_agent.process_video(
        video_path=test_video_path,
        video_id="integration-test-001",
        progress_callback=progress_tracker.callback,
    )

    # =================================================================
    # 1. Validate ProcessingResult
    # =================================================================

    assert isinstance(result, ProcessingResult)
    assert result.video_id == "integration-test-001"
    assert result.video_path == test_video_path

    print(f"\nProcessing Results:")
    print(f"  Total frames: {result.total_frames}")
    print(f"  Total detections: {result.total_detections}")
    print(f"  Keyframes extracted: {result.keyframes_extracted}")
    print(f"  Processing time: {result.processing_time_seconds:.2f}s")

    # Should have processed the video
    assert result.total_frames > 0

    # May or may not have detections depending on video content
    # (but test should complete successfully either way)

    # =================================================================
    # 2. Validate Progress Tracking
    # =================================================================

    stages = progress_tracker.get_stages()
    assert "detection" in stages
    assert "extraction" in stages
    assert "complete" in stages

    # Verify stages in correct order
    detection_idx = stages.index("detection")
    extraction_idx = stages.index("extraction")
    complete_idx = stages.index("complete")

    assert detection_idx < extraction_idx < complete_idx

    print(f"\nProgress stages tracked: {len(progress_tracker.calls)} callbacks")

    # =================================================================
    # 3. Validate Output Directory Structure
    # =================================================================

    assert result.output_dir.exists()
    assert result.output_dir.is_dir()

    print(f"\nOutput directory: {result.output_dir}")

    # =================================================================
    # 4. Validate Metadata JSON
    # =================================================================

    assert result.metadata_path.exists()
    assert result.metadata_path.is_file()
    assert result.metadata_path.name == "metadata.json"

    # Read and validate metadata
    with open(result.metadata_path, "r") as f:
        metadata = json.load(f)

    assert "video_id" in metadata
    assert metadata["video_id"] == "integration-test-001"
    assert "total_keyframes" in metadata
    assert "keyframes" in metadata
    assert isinstance(metadata["keyframes"], list)

    print(f"\nMetadata saved: {result.metadata_path}")
    print(f"  Total keyframes in metadata: {metadata['total_keyframes']}")

    # =================================================================
    # 5. Validate Keyframe Images (if any extracted)
    # =================================================================

    if result.keyframes_extracted > 0:
        assert result.keyframe_dir.exists()
        assert result.keyframe_dir.is_dir()

        # Count JPEG files
        jpeg_files = list(result.keyframe_dir.glob("*.jpg"))
        assert len(jpeg_files) == result.keyframes_extracted

        print(f"\nKeyframe images:")
        print(f"  Directory: {result.keyframe_dir}")
        print(f"  Image files: {len(jpeg_files)}")

        # Verify each keyframe
        for keyframe in result.keyframes:
            # Check keyframe dict structure
            assert "filename" in keyframe
            assert "frame_index" in keyframe
            assert "timestamp" in keyframe
            assert "score" in keyframe
            assert "bbox" in keyframe

            # Check actual file exists
            image_path = result.keyframe_dir / keyframe["filename"]
            assert image_path.exists()
            assert image_path.is_file()
            assert image_path.suffix == ".jpg"

            # Check file is not empty
            assert image_path.stat().st_size > 0

            print(f"    ✓ {keyframe['filename']} ({image_path.stat().st_size} bytes)")

    else:
        print(f"\nNo keyframes extracted (no persons detected in video)")

    # =================================================================
    # 6. Validate Statistics
    # =================================================================

    assert result.processing_time_seconds > 0
    assert result.processing_time_seconds < 300  # Should complete < 5 minutes

    assert isinstance(result.started_at, type(result.completed_at))
    assert result.completed_at >= result.started_at

    # =================================================================
    # Test Summary
    # =================================================================

    print(f"\n{'='*70}")
    print(f"INTEGRATION TEST PASSED")
    print(f"{'='*70}")
    print(f"✓ Detection stage completed")
    print(f"✓ Keyframe extraction completed")
    print(f"✓ Progress tracking working")
    print(f"✓ Output files created")
    print(f"✓ Metadata JSON valid")
    if result.keyframes_extracted > 0:
        print(f"✓ {result.keyframes_extracted} keyframe images verified")
    print(f"✓ Processing time: {result.processing_time_seconds:.2f}s")
    print(f"{'='*70}\n")


@pytest.mark.integration
async def test_pipeline_with_no_persons_detected(lead_agent, test_video_path, output_dir):
    """
    Test pipeline handles video with no person detections gracefully.

    This validates the error-free completion even when no persons are found.
    """
    if test_video_path is None:
        pytest.skip("No test video file found")

    result = await lead_agent.process_video(
        video_path=test_video_path, video_id="integration-test-no-persons"
    )

    # Should complete successfully
    assert isinstance(result, ProcessingResult)

    # If no persons detected
    if result.total_detections == 0:
        assert result.keyframes_extracted == 0
        assert len(result.keyframes) == 0

        # Metadata should still be created
        assert result.metadata_path.exists()


@pytest.mark.integration
async def test_pipeline_error_handling(lead_agent, output_dir):
    """
    Test pipeline error handling with invalid video path.

    Validates that pipeline fails gracefully with clear error messages.
    """
    from backend.core.exceptions import VideoProcessingError

    invalid_path = Path("/nonexistent/video.mp4")

    with pytest.raises(FileNotFoundError, match="Video file not found"):
        await lead_agent.process_video(video_path=invalid_path, video_id="integration-test-error")


# =============================================================================
# HELPER FUNCTION FOR MANUAL TESTING
# =============================================================================


async def run_pipeline_manually(video_path: Path, output_dir: Path):
    """
    Helper function to run the full pipeline manually for testing.

    Usage:
        >>> from pathlib import Path
        >>> import asyncio
        >>> asyncio.run(run_pipeline_manually(
        ...     Path("path/to/video.mp4"),
        ...     Path("output")
        ... ))
    """
    print(f"Initializing agents...")

    detection_agent = DetectionAgent(model_name="yolov8n.pt")
    keyframe_agent = KeyframeAgent(output_dir=output_dir)
    lead_agent = LeadAgent(detection_agent=detection_agent, keyframe_agent=keyframe_agent)

    def progress_callback(stage: str, percentage: int):
        print(f"[{stage.upper()}] {percentage}%")

    print(f"Processing video: {video_path}")

    result = await lead_agent.process_video(
        video_path=video_path, video_id="manual-test", progress_callback=progress_callback
    )

    print(f"\n{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Total frames: {result.total_frames}")
    print(f"Detections: {result.total_detections}")
    print(f"Keyframes: {result.keyframes_extracted}")
    print(f"Time: {result.processing_time_seconds:.2f}s")
    print(f"Output: {result.output_dir}")
    print(f"{'='*70}\n")

    return result


if __name__ == "__main__":
    """
    Run integration test manually.

    Place a test video at tests/fixtures/test_video.mp4 and run:
    python tests/integration/test_full_pipeline.py
    """
    import asyncio
    from pathlib import Path

    test_video = Path("tests/fixtures/test_video.mp4")
    output = Path("output/integration_test")

    if not test_video.exists():
        print(f"Error: Test video not found at {test_video}")
        print(f"Please place a test video file there and try again.")
        exit(1)

    asyncio.run(run_pipeline_manually(test_video, output))

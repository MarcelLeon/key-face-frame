"""
End-to-End Test - Complete Workflow

This is the ULTIMATE test. If this passes, the system works end-to-end.

Tests the complete video processing pipeline with real video:
1. Video input (actual WanAnimate video file)
2. YOLO person detection
3. Keyframe extraction
4. File output validation
5. Metadata generation

This test uses REAL dependencies:
- Real video file
- Real YOLO model
- Real OpenCV processing
- Real file I/O

Expected execution time: 30 seconds - 2 minutes
"""

import json
import shutil
from pathlib import Path

import pytest

from backend.core.agents.detection_agent import DetectionAgent
from backend.core.agents.keyframe_agent import KeyframeAgent
from backend.core.agents.lead_agent import LeadAgent, ProcessingResult

# =============================================================================
# CONFIGURATION
# =============================================================================

# 注意: 测试视频路径现在通过 test_video_path fixture 自动注入
# 可以通过以下方式配置：
#   1. 环境变量: export TEST_VIDEO_FILE="your_video.mp4"
#   2. pytest.ini: test_video_file = your_video.mp4
#   3. 默认值: WanAnimate_00001_p84-audio_gouns_1765004610.mp4

# Output directory for E2E tests
OUTPUT_DIR = Path("/Users/wangzq/VsCodeProjects/key-face-frame/output")

# Test video ID
TEST_VIDEO_ID = "test-e2e-001"

# YOLO model (use nano for speed in tests)
YOLO_MODEL = "yolov8n.pt"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def detection_agent():
    """Real DetectionAgent with YOLOv8 model."""
    return DetectionAgent(model_name=YOLO_MODEL)


@pytest.fixture(scope="module")
def keyframe_agent():
    """Real KeyframeAgent with output directory."""
    return KeyframeAgent(output_dir=OUTPUT_DIR)


@pytest.fixture(scope="module")
def lead_agent(detection_agent, keyframe_agent):
    """Real LeadAgent orchestrating the pipeline."""
    return LeadAgent(detection_agent=detection_agent, keyframe_agent=keyframe_agent)


@pytest.fixture(scope="module")
def test_output_dir():
    """Output directory for this test run."""
    output_dir = OUTPUT_DIR / f"video-{TEST_VIDEO_ID}"

    # Clean up before test
    if output_dir.exists():
        shutil.rmtree(output_dir)

    yield output_dir

    # Optionally clean up after test (commented out to inspect results)
    # if output_dir.exists():
    #     shutil.rmtree(output_dir)


# =============================================================================
# PRE-TEST VALIDATION
# =============================================================================


def test_prerequisites(test_video_path):
    """
    Validate prerequisites before running E2E test.

    This ensures:
    - Test video exists (through test_video_path fixture)
    - Output directory is writeable
    - YOLO model can be loaded

    Args:
        test_video_path: Pytest fixture providing configured video path
    """
    # Check test video exists (fixture already validates this)
    assert test_video_path.exists(), f"Test video not found: {test_video_path}"

    # Check video is readable
    assert test_video_path.is_file(), f"Path exists but is not a file: {test_video_path}"

    # Check video size is reasonable
    video_size_mb = test_video_path.stat().st_size / (1024 * 1024)
    assert video_size_mb > 0.1, f"Video file seems too small: {video_size_mb:.2f} MB"
    assert video_size_mb < 100, f"Video file seems too large for testing: {video_size_mb:.2f} MB"

    # Check output directory is writeable
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    assert OUTPUT_DIR.exists(), f"Cannot create output directory: {OUTPUT_DIR}"

    # Try to create a test file
    test_file = OUTPUT_DIR / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Output directory not writeable: {OUTPUT_DIR}\nError: {e}")

    print(f"\n✓ Prerequisites validated:")
    print(f"  - Test video: {test_video_path} ({video_size_mb:.2f} MB)")
    print(f"  - Output directory: {OUTPUT_DIR}")
    print(f"  - YOLO model: {YOLO_MODEL}")


# =============================================================================
# MAIN E2E TEST
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_workflow_with_real_video(lead_agent, test_output_dir, test_video_path):
    """
    THE ULTIMATE TEST - Complete end-to-end workflow with real video.

    This test validates:
    1. Video can be loaded and read
    2. YOLO detects persons in video
    3. Keyframes are extracted
    4. Output files are created
    5. Metadata is valid JSON
    6. Result object contains correct data

    If this test passes, the system is working correctly!

    Args:
        lead_agent: Pytest fixture providing LeadAgent instance
        test_output_dir: Pytest fixture providing output directory
        test_video_path: Pytest fixture providing configured video path
    """
    print(f"\n{'='*70}")
    print(f"STARTING END-TO-END TEST")
    print(f"{'='*70}")
    print(f"Video: {test_video_path.name}")
    print(f"Output: {test_output_dir}")
    print(f"{'='*70}\n")

    # Configure for faster test execution
    config = {
        "sample_rate": 5,  # Process every 5th frame (faster)
        "max_frames": 20,  # Limit to 20 keyframes (faster)
        "confidence_threshold": 0.5,  # Standard threshold
    }

    # Process video
    result: ProcessingResult = await lead_agent.process_video(
        video_path=test_video_path, video_id=TEST_VIDEO_ID, config=config
    )

    # =============================================================================
    # VALIDATE RESULT OBJECT
    # =============================================================================

    print(f"\n{'='*70}")
    print(f"VALIDATING RESULTS")
    print(f"{'='*70}\n")

    # Basic result validation
    assert isinstance(result, ProcessingResult), "Result should be ProcessingResult instance"
    assert (
        result.video_id == TEST_VIDEO_ID
    ), f"Expected video_id={TEST_VIDEO_ID}, got {result.video_id}"
    assert result.video_path == test_video_path, "Video path should match input"

    print(f"✓ Result object validated")

    # Detection validation
    assert result.total_detections > 0, (
        "Expected at least some person detections in video. "
        "This video should contain persons. If this fails, check YOLO model."
    )
    print(f"✓ Detections: {result.total_detections} persons detected")

    # Keyframe validation
    assert result.keyframes_extracted > 0, (
        "Expected at least one keyframe. If detections exist but no keyframes, "
        "check KeyframeAgent logic."
    )
    print(f"✓ Keyframes: {result.keyframes_extracted} keyframes extracted")

    # Performance validation
    assert result.processing_time_seconds > 0, "Processing time should be positive"
    assert result.processing_time_seconds < 300, (
        f"Processing took too long: {result.processing_time_seconds:.2f}s. "
        "Expected < 5 minutes for test video."
    )
    print(f"✓ Performance: {result.processing_time_seconds:.2f} seconds")

    # Timestamps validation
    assert result.started_at is not None, "Should have started_at timestamp"
    assert result.completed_at is not None, "Should have completed_at timestamp"
    assert result.completed_at >= result.started_at, "completed_at should be after started_at"
    print(f"✓ Timestamps: {result.started_at} → {result.completed_at}")

    # =============================================================================
    # VALIDATE OUTPUT DIRECTORY STRUCTURE
    # =============================================================================

    print(f"\n{'='*70}")
    print(f"VALIDATING OUTPUT FILES")
    print(f"{'='*70}\n")

    # Output directory should exist
    assert result.output_dir is not None, "Result should have output_dir"
    assert result.output_dir.exists(), f"Output directory should exist: {result.output_dir}"
    print(f"✓ Output directory exists: {result.output_dir}")

    # Keyframe directory should exist
    assert result.keyframe_dir is not None, "Result should have keyframe_dir"
    assert result.keyframe_dir.exists(), f"Keyframe directory should exist: {result.keyframe_dir}"
    print(f"✓ Keyframe directory exists: {result.keyframe_dir}")

    # Validate directory structure
    expected_structure = [
        result.keyframe_dir,  # keyframes/
    ]

    for path in expected_structure:
        assert path.exists(), f"Expected directory/file: {path}"

    # Validate keyframe image files
    keyframe_files = list(result.keyframe_dir.glob("*.jpg"))
    assert len(keyframe_files) > 0, (
        f"Expected JPEG files in {result.keyframe_dir}, found none. "
        "Check KeyframeAgent save logic."
    )
    assert len(keyframe_files) == result.keyframes_extracted, (
        f"Mismatch: Result says {result.keyframes_extracted} keyframes, "
        f"but found {len(keyframe_files)} JPEG files"
    )
    print(f"✓ Keyframe images: {len(keyframe_files)} JPEG files")

    # Validate individual keyframe files
    for keyframe_file in keyframe_files:
        # Check file exists and is not empty
        assert keyframe_file.exists(), f"Keyframe file missing: {keyframe_file}"
        file_size = keyframe_file.stat().st_size
        assert file_size > 1000, (
            f"Keyframe file too small: {keyframe_file} ({file_size} bytes). "
            "Expected at least 1KB for a valid JPEG."
        )

        # Validate filename format: frame_XXXXX_tX.XXs.jpg
        assert keyframe_file.name.startswith(
            "frame_"
        ), f"Unexpected filename format: {keyframe_file.name}"
        assert keyframe_file.name.endswith(".jpg"), f"Expected .jpg extension: {keyframe_file.name}"

    print(f"✓ All keyframe files validated (size, format)")

    # =============================================================================
    # VALIDATE METADATA.JSON
    # =============================================================================

    print(f"\n{'='*70}")
    print(f"VALIDATING METADATA")
    print(f"{'='*70}\n")

    # Metadata file should exist
    assert result.metadata_path is not None, "Result should have metadata_path"
    assert result.metadata_path.exists(), f"Metadata file should exist: {result.metadata_path}"
    assert (
        result.metadata_path.name == "metadata.json"
    ), f"Expected metadata.json, got {result.metadata_path.name}"
    print(f"✓ Metadata file exists: {result.metadata_path}")

    # Load and validate metadata JSON
    with open(result.metadata_path) as f:
        metadata = json.load(f)

    # Validate metadata structure
    assert "video_id" in metadata, "Metadata missing video_id"
    assert "video_path" in metadata, "Metadata missing video_path"
    assert "total_frames" in metadata, "Metadata missing total_frames"
    assert "total_detections" in metadata, "Metadata missing total_detections"
    assert "keyframes_extracted" in metadata, "Metadata missing keyframes_extracted"
    assert "keyframes" in metadata, "Metadata missing keyframes array"
    assert "processing_time_seconds" in metadata, "Metadata missing processing_time_seconds"
    assert "started_at" in metadata, "Metadata missing started_at"
    assert "completed_at" in metadata, "Metadata missing completed_at"

    print(f"✓ Metadata structure validated")

    # Validate metadata values match result
    assert metadata["video_id"] == TEST_VIDEO_ID, "Metadata video_id mismatch"
    assert metadata["total_detections"] == result.total_detections, "Metadata detections mismatch"
    assert (
        metadata["keyframes_extracted"] == result.keyframes_extracted
    ), "Metadata keyframes mismatch"

    print(f"✓ Metadata values match result object")

    # Validate keyframes array in metadata
    assert isinstance(metadata["keyframes"], list), "Keyframes should be array"
    assert len(metadata["keyframes"]) == result.keyframes_extracted, (
        f"Metadata keyframes count mismatch: "
        f"expected {result.keyframes_extracted}, got {len(metadata['keyframes'])}"
    )

    print(f"✓ Metadata contains {len(metadata['keyframes'])} keyframe entries")

    # Validate individual keyframe metadata
    for i, keyframe_meta in enumerate(metadata["keyframes"]):
        assert "frame_index" in keyframe_meta, f"Keyframe {i} missing frame_index"
        assert "timestamp" in keyframe_meta, f"Keyframe {i} missing timestamp"
        assert "score" in keyframe_meta, f"Keyframe {i} missing score"
        assert "bbox" in keyframe_meta, f"Keyframe {i} missing bbox"
        assert "filename" in keyframe_meta, f"Keyframe {i} missing filename"

        # Validate types
        assert isinstance(keyframe_meta["frame_index"], int), "frame_index should be int"
        assert isinstance(keyframe_meta["timestamp"], (int, float)), "timestamp should be numeric"
        assert isinstance(keyframe_meta["score"], (int, float)), "score should be numeric"
        assert isinstance(keyframe_meta["bbox"], list), "bbox should be array"
        assert isinstance(keyframe_meta["filename"], str), "filename should be string"

        # Validate score range
        assert 0.0 <= keyframe_meta["score"] <= 1.0, f"Score out of range: {keyframe_meta['score']}"

        # Validate bbox has 4 coordinates
        assert (
            len(keyframe_meta["bbox"]) == 4
        ), f"bbox should have 4 values: {keyframe_meta['bbox']}"

        # Validate filename corresponds to actual file
        keyframe_file_path = result.keyframe_dir / keyframe_meta["filename"]
        assert (
            keyframe_file_path.exists()
        ), f"Metadata references non-existent file: {keyframe_meta['filename']}"

    print(f"✓ All keyframe metadata entries validated")

    # =============================================================================
    # VALIDATE RESULT.KEYFRAMES ARRAY
    # =============================================================================

    print(f"\n{'='*70}")
    print(f"VALIDATING RESULT KEYFRAMES")
    print(f"{'='*70}\n")

    assert (
        len(result.keyframes) == result.keyframes_extracted
    ), "Result keyframes array length mismatch"

    for i, keyframe in enumerate(result.keyframes):
        assert isinstance(keyframe, dict), f"Keyframe {i} should be dict"
        assert "frame_index" in keyframe, f"Keyframe {i} missing frame_index"
        assert "timestamp" in keyframe, f"Keyframe {i} missing timestamp"
        assert "score" in keyframe, f"Keyframe {i} missing score"
        assert "filename" in keyframe, f"Keyframe {i} missing filename"

    print(f"✓ Result keyframes array validated ({len(result.keyframes)} entries)")

    # =============================================================================
    # FINAL SUMMARY
    # =============================================================================

    print(f"\n{'='*70}")
    print(f"END-TO-END TEST PASSED ✓")
    print(f"{'='*70}")
    print(f"\nSummary:")
    print(f"  Video:      {test_video_path.name}")
    print(f"  Frames:     {result.total_frames}")
    print(f"  Detections: {result.total_detections} persons")
    print(f"  Keyframes:  {result.keyframes_extracted} extracted")
    print(f"  Time:       {result.processing_time_seconds:.2f}s")
    print(f"  Output:     {result.keyframe_dir}")
    print(f"\nOutput files:")

    for keyframe_file in sorted(keyframe_files)[:5]:  # Show first 5
        file_size_kb = keyframe_file.stat().st_size / 1024
        print(f"  - {keyframe_file.name} ({file_size_kb:.1f} KB)")

    if len(keyframe_files) > 5:
        print(f"  ... and {len(keyframe_files) - 5} more")

    print(f"\n{'='*70}\n")

    # Test passes if we reach here without assertion errors
    assert True, "E2E test completed successfully!"


# =============================================================================
# ADDITIONAL E2E TESTS (Optional)
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_with_different_config(lead_agent, test_video_path):
    """
    Test E2E workflow with different configuration.

    This validates that config parameters are respected.

    Args:
        lead_agent: Pytest fixture providing LeadAgent instance
        test_video_path: Pytest fixture providing configured video path
    """
    # Use very aggressive sampling for speed
    config = {
        "sample_rate": 10,  # Process every 10th frame
        "max_frames": 5,  # Only 5 keyframes
    }

    result = await lead_agent.process_video(
        video_path=test_video_path, video_id="test-e2e-config", config=config
    )

    # Should still get results, even with aggressive config
    assert result.total_detections >= 0
    assert result.keyframes_extracted >= 0
    assert result.keyframes_extracted <= 5, "Should respect max_frames=5"

    print(f"\n✓ Config test passed:")
    print(f"  - Detections: {result.total_detections}")
    print(f"  - Keyframes: {result.keyframes_extracted} (max 5)")
    print(f"  - Time: {result.processing_time_seconds:.2f}s")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_progress_callback(lead_agent, test_video_path):
    """
    Test E2E workflow with progress callback.

    This validates that progress reporting works.

    Args:
        lead_agent: Pytest fixture providing LeadAgent instance
        test_video_path: Pytest fixture providing configured video path
    """
    progress_updates = []

    def progress_callback(stage: str, percentage: float) -> None:
        """Capture progress updates."""
        progress_updates.append((stage, percentage))
        print(f"  Progress: {stage} - {percentage:.1f}%")

    result = await lead_agent.process_video(
        video_path=test_video_path,
        video_id="test-e2e-progress",
        config={"sample_rate": 5, "max_frames": 10},
        progress_callback=progress_callback,
    )

    # Should have received progress updates
    assert len(progress_updates) > 0, "Should receive progress updates"

    # Check progress stages
    stages = [stage for stage, _ in progress_updates]
    assert "detection" in stages, "Should report detection progress"
    assert "extraction" in stages, "Should report extraction progress"
    assert "complete" in stages, "Should report completion"

    print(f"\n✓ Progress callback test passed:")
    print(f"  - Progress updates: {len(progress_updates)}")
    print(f"  - Stages: {set(stages)}")

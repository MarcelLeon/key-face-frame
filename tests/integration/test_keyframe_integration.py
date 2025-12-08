"""
Keyframe Integration Tests

End-to-end integration tests for KeyframeAgent with real video processing.
Tests the complete pipeline: DetectionAgent → KeyframeAgent.
"""

import json
from pathlib import Path
from typing import List

import pytest

from backend.core.agents.detection_agent import DetectionAgent
from backend.core.agents.keyframe_agent import Keyframe, KeyframeAgent


@pytest.mark.integration
@pytest.mark.slow
class TestKeyframeIntegration:
    """Integration tests for keyframe extraction with real video."""

    @pytest.mark.asyncio
    async def test_keyframe_extraction_with_real_video(self, tmp_path: Path):
        """
        Integration test: DetectionAgent → KeyframeAgent

        1. Use DetectionAgent to detect persons in test video
        2. Use KeyframeAgent to extract keyframes
        3. Verify:
           - Images saved to correct directory
           - metadata.json created and valid
           - JPEG files readable
           - Number of keyframes <= max_frames
        """
        # Setup test video path (assumes test video exists)
        test_video = Path(__file__).parent.parent / "fixtures" / "test_video.mp4"

        # Skip if test video doesn't exist
        if not test_video.exists():
            pytest.skip(f"Test video not found: {test_video}")

        # Setup output directory
        output_dir = tmp_path / "keyframes_output"
        output_dir.mkdir()

        # Phase 1: Run DetectionAgent to get person detections
        detection_agent = DetectionAgent(model_name="yolov8n.pt", confidence_threshold=0.5)

        detections = await detection_agent.process_video(
            video_path=test_video,
            sample_rate=5,  # Process every 5th frame for speed
        )

        # Verify we got detections
        assert len(detections) > 0, "No persons detected in test video"

        print(f"Detected {len(detections)} persons in video")

        # Convert Detection objects to dicts for KeyframeAgent
        detection_dicts = [
            {
                "frame_index": d.frame_index,
                "timestamp": d.timestamp,
                "bbox": d.bbox,
                "confidence": d.confidence,
                "track_id": d.track_id,
            }
            for d in detections
        ]

        # Phase 2: Run KeyframeAgent to extract keyframes
        keyframe_agent = KeyframeAgent(output_dir=output_dir, time_threshold=1.0, jpeg_quality=95)

        max_frames = 10
        keyframes = await keyframe_agent.extract_keyframes(
            video_path=test_video,
            detections=detection_dicts,
            video_id="test-integration",
            max_frames=max_frames,
        )

        # Verify results
        assert isinstance(keyframes, list)
        assert len(keyframes) > 0, "No keyframes extracted"
        assert len(keyframes) <= max_frames, f"Too many keyframes: {len(keyframes)} > {max_frames}"

        print(f"Extracted {len(keyframes)} keyframes")

        # Verify output directory structure
        video_output = output_dir / "video-test-integration"
        assert video_output.exists(), "Video output directory not created"

        keyframes_dir = video_output / "keyframes"
        assert keyframes_dir.exists(), "Keyframes directory not created"

        # Verify metadata.json
        metadata_path = video_output / "metadata.json"
        assert metadata_path.exists(), "metadata.json not created"

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        assert metadata["video_id"] == "test-integration"
        assert metadata["total_keyframes"] == len(keyframes)
        assert "extraction_params" in metadata
        assert metadata["extraction_params"]["max_frames"] == max_frames

        # Verify JPEG files are saved and readable
        jpg_files = list(keyframes_dir.glob("*.jpg"))
        assert len(jpg_files) == len(keyframes), "JPEG count mismatch"

        for jpg_file in jpg_files:
            # Verify file is not empty
            assert jpg_file.stat().st_size > 0, f"Empty JPEG file: {jpg_file}"

            # Verify file is readable as image
            import cv2

            img = cv2.imread(str(jpg_file))
            assert img is not None, f"Cannot read JPEG: {jpg_file}"
            assert img.shape[0] > 0 and img.shape[1] > 0, f"Invalid image dimensions: {jpg_file}"

        # Verify all keyframes have required attributes
        for kf in keyframes:
            assert isinstance(kf, Keyframe)
            assert kf.frame_index >= 0
            assert kf.timestamp >= 0.0
            assert kf.score >= 0.0
            assert len(kf.bbox) == 4
            assert kf.filename.endswith(".jpg")

            # Verify filename matches expected format
            expected_prefix = f"frame_{kf.frame_index:05d}_t{kf.timestamp:.2f}s"
            assert kf.filename.startswith(expected_prefix)

            # Verify file exists
            file_path = keyframes_dir / kf.filename
            assert file_path.exists(), f"Keyframe file not found: {kf.filename}"

        print("All integration tests passed!")

    @pytest.mark.asyncio
    async def test_keyframe_extraction_with_progress_callback(self, tmp_path: Path):
        """Test keyframe extraction with progress tracking."""
        test_video = Path(__file__).parent.parent / "fixtures" / "test_video.mp4"

        if not test_video.exists():
            pytest.skip(f"Test video not found: {test_video}")

        output_dir = tmp_path / "keyframes_output"
        output_dir.mkdir()

        # Get detections
        detection_agent = DetectionAgent(model_name="yolov8n.pt")
        detections = await detection_agent.process_video(
            video_path=test_video,
            sample_rate=10,
        )

        if len(detections) == 0:
            pytest.skip("No detections found in test video")

        detection_dicts = [
            {
                "frame_index": d.frame_index,
                "timestamp": d.timestamp,
                "bbox": d.bbox,
                "confidence": d.confidence,
                "track_id": d.track_id,
            }
            for d in detections
        ]

        # Track progress
        progress_updates = []

        def progress_callback(current: int, total: int):
            progress_updates.append((current, total))
            print(f"Progress: {current}/{total} ({100 * current / total:.1f}%)")

        # Extract keyframes with progress tracking
        keyframe_agent = KeyframeAgent(output_dir=output_dir)

        keyframes = await keyframe_agent.extract_keyframes(
            video_path=test_video,
            detections=detection_dicts,
            video_id="test-progress",
            max_frames=5,
            progress_callback=progress_callback,
        )

        # Verify progress callback was called
        assert len(progress_updates) > 0, "Progress callback not called"

        # Verify progress increases monotonically
        for i in range(len(progress_updates) - 1):
            current1, total1 = progress_updates[i]
            current2, total2 = progress_updates[i + 1]

            assert current2 >= current1, "Progress should increase"
            assert total1 == total2, "Total should remain constant"

        # Verify final progress is 100%
        final_current, final_total = progress_updates[-1]
        assert final_current == final_total, "Should reach 100% progress"
        assert final_total == len(keyframes)

    @pytest.mark.asyncio
    async def test_keyframe_deduplication(self, tmp_path: Path):
        """Test that temporal deduplication works correctly."""
        test_video = Path(__file__).parent.parent / "fixtures" / "test_video.mp4"

        if not test_video.exists():
            pytest.skip(f"Test video not found: {test_video}")

        output_dir = tmp_path / "keyframes_output"
        output_dir.mkdir()

        # Get detections with high sampling (many frames)
        detection_agent = DetectionAgent(model_name="yolov8n.pt")
        detections = await detection_agent.process_video(
            video_path=test_video,
            sample_rate=1,  # Process all frames
        )

        if len(detections) < 10:
            pytest.skip("Not enough detections for deduplication test")

        detection_dicts = [
            {
                "frame_index": d.frame_index,
                "timestamp": d.timestamp,
                "bbox": d.bbox,
                "confidence": d.confidence,
                "track_id": d.track_id,
            }
            for d in detections
        ]

        # Extract with strict time threshold (should filter many duplicates)
        keyframe_agent = KeyframeAgent(
            output_dir=output_dir,
            time_threshold=2.0,  # 2 second minimum gap
        )

        keyframes = await keyframe_agent.extract_keyframes(
            video_path=test_video,
            detections=detection_dicts,
            video_id="test-dedup",
            max_frames=100,
        )

        # Verify temporal spacing
        if len(keyframes) > 1:
            # Sort by timestamp
            sorted_keyframes = sorted(keyframes, key=lambda x: x.timestamp)

            # Check all consecutive frames are at least time_threshold apart
            for i in range(len(sorted_keyframes) - 1):
                time_diff = sorted_keyframes[i + 1].timestamp - sorted_keyframes[i].timestamp
                assert (
                    time_diff >= keyframe_agent.time_threshold
                ), f"Frames too close: {time_diff}s < {keyframe_agent.time_threshold}s"

        print(f"Deduplication test passed: {len(keyframes)} unique keyframes")

    @pytest.mark.asyncio
    async def test_keyframe_quality_scoring(self, tmp_path: Path):
        """Test that keyframes are scored correctly (higher quality first)."""
        test_video = Path(__file__).parent.parent / "fixtures" / "test_video.mp4"

        if not test_video.exists():
            pytest.skip(f"Test video not found: {test_video}")

        output_dir = tmp_path / "keyframes_output"
        output_dir.mkdir()

        # Get detections
        detection_agent = DetectionAgent(model_name="yolov8n.pt")
        detections = await detection_agent.process_video(
            video_path=test_video,
            sample_rate=5,
        )

        if len(detections) < 3:
            pytest.skip("Not enough detections for scoring test")

        detection_dicts = [
            {
                "frame_index": d.frame_index,
                "timestamp": d.timestamp,
                "bbox": d.bbox,
                "confidence": d.confidence,
                "track_id": d.track_id,
            }
            for d in detections
        ]

        # Extract keyframes
        keyframe_agent = KeyframeAgent(output_dir=output_dir)

        keyframes = await keyframe_agent.extract_keyframes(
            video_path=test_video,
            detections=detection_dicts,
            video_id="test-scoring",
            max_frames=min(10, len(detections)),
        )

        # Verify keyframes are returned in score order (descending)
        # Note: metadata should preserve the score order
        metadata_path = output_dir / "video-test-scoring" / "metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        scores = [kf["score"] for kf in metadata["keyframes"]]

        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert (
                scores[i] >= scores[i + 1]
            ), f"Scores not in descending order: {scores[i]} < {scores[i+1]}"

        print(f"Quality scoring test passed: scores = {scores}")

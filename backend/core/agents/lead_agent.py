"""
Lead Agent

Orchestrates the multi-agent video processing pipeline.
Coordinates DetectionAgent and KeyframeAgent to process videos.
Handles progress tracking, error management, and result aggregation.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import cv2

from backend.core.agents.detection_agent import Detection, DetectionAgent
from backend.core.agents.keyframe_agent import Keyframe, KeyframeAgent
from backend.core.exceptions import VideoProcessingError

# Configure logging
logger = logging.getLogger(__name__)


# Stage constants
STAGE_DETECTION = "detection"
STAGE_EXTRACTION = "extraction"
STAGE_COMPLETE = "complete"


@dataclass
class ProcessingResult:
    """Result of video processing."""

    video_id: str
    video_path: Path

    # Statistics
    total_frames: int
    total_detections: int
    keyframes_extracted: int
    processing_time_seconds: float

    # Output paths
    output_dir: Path
    keyframe_dir: Path
    metadata_path: Path

    # Keyframe details
    keyframes: List[Dict[str, Any]]  # List of keyframe metadata dicts

    # Timestamps
    started_at: datetime
    completed_at: datetime


class LeadAgent:
    """
    Lead orchestrator agent for video keyframe extraction.

    Coordinates DetectionAgent and KeyframeAgent to process videos.
    Handles progress tracking, error management, and result aggregation.

    This agent is purely an orchestrator - it does NOT perform detection
    or extraction itself, only coordinates other agents.

    Attributes:
        detection_agent: DetectionAgent instance for person detection
        keyframe_agent: KeyframeAgent instance for keyframe extraction
        default_config: Default processing configuration

    Example:
        >>> detection_agent = DetectionAgent(model_name="yolov8m.pt")
        >>> keyframe_agent = KeyframeAgent(output_dir=Path("output"))
        >>> lead_agent = LeadAgent(
        ...     detection_agent=detection_agent,
        ...     keyframe_agent=keyframe_agent
        ... )
        >>> result = await lead_agent.process_video(
        ...     video_path=Path("video.mp4"),
        ...     video_id="video-123"
        ... )
        >>> print(f"Extracted {result.keyframes_extracted} keyframes")
    """

    def __init__(
        self,
        detection_agent: Optional[DetectionAgent],
        keyframe_agent: Optional[KeyframeAgent],
        default_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize lead agent.

        Args:
            detection_agent: Initialized DetectionAgent instance
            keyframe_agent: Initialized KeyframeAgent instance
            default_config: Default processing configuration
                - sample_rate: int (default 1)
                - max_frames: int (default 100)
                - confidence_threshold: float (default 0.5)

        Raises:
            ValueError: If agents not provided
        """
        if detection_agent is None:
            raise ValueError("detection_agent is required")

        if keyframe_agent is None:
            raise ValueError("keyframe_agent is required")

        self.detection_agent = detection_agent
        self.keyframe_agent = keyframe_agent

        # Set default configuration
        if default_config is None:
            self.default_config = {
                "sample_rate": 1,
                "max_frames": 100,
                "confidence_threshold": 0.5,
            }
        else:
            self.default_config = default_config

        logger.info(f"LeadAgent initialized with default config: {self.default_config}")

    async def process_video(
        self,
        video_path: Path,
        video_id: str,
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> ProcessingResult:
        """
        Process video through complete pipeline.

        Pipeline stages:
        1. Validate video exists
        2. Run DetectionAgent (detect persons)
        3. Run KeyframeAgent (extract keyframes)
        4. Aggregate results

        Args:
            video_path: Path to video file
            video_id: Unique identifier for this processing job
            config: Optional config overrides
            progress_callback: Callback(stage_name, progress_percent)

        Returns:
            ProcessingResult with all metadata and output paths

        Raises:
            VideoProcessingError: If pipeline fails
            FileNotFoundError: If video doesn't exist
        """
        started_at = datetime.now()
        start_time = time.time()

        logger.info(f"Starting video processing: video_id={video_id}, " f"video_path={video_path}")

        try:
            # 1. Validate video path
            self._validate_video_path(video_path)

            # 2. Merge configuration
            merged_config = self._merge_config(config)
            logger.debug(f"Merged config: {merged_config}")

            # 3. Get video metadata
            total_frames = self._get_total_frames(video_path)

            # 4. Detection stage
            logger.info("Starting detection stage")
            if progress_callback:
                progress_callback(STAGE_DETECTION, 0)

            try:
                detections = await self.detection_agent.process_video(
                    video_path=video_path,
                    sample_rate=merged_config["sample_rate"],
                )
            except Exception as e:
                logger.error(f"Detection stage failed: {e}", exc_info=True)
                if isinstance(e, VideoProcessingError):
                    raise
                raise VideoProcessingError(f"Detection stage failed: {e}") from e

            total_detections = len(detections)
            logger.info(f"Detection complete: {total_detections} detections")

            if progress_callback:
                progress_callback(STAGE_DETECTION, 100)

            # 5. Extraction stage
            logger.info("Starting keyframe extraction stage")
            if progress_callback:
                progress_callback(STAGE_EXTRACTION, 0)

            # Convert Detection objects to dicts
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

            try:
                keyframes = await self.keyframe_agent.extract_keyframes(
                    video_path=video_path,
                    detections=detection_dicts,
                    video_id=video_id,
                    max_frames=merged_config["max_frames"],
                )
            except Exception as e:
                logger.error(f"Keyframe extraction stage failed: {e}", exc_info=True)
                raise  # Re-raise KeyframeExtractionError directly

            keyframes_extracted = len(keyframes)
            logger.info(f"Extraction complete: {keyframes_extracted} keyframes")

            if progress_callback:
                progress_callback(STAGE_EXTRACTION, 100)

            # 6. Build result
            completed_at = datetime.now()
            processing_time = time.time() - start_time

            # Convert Keyframe objects to dicts
            keyframe_dicts = [asdict(kf) for kf in keyframes]

            # Determine output paths
            output_dir = self.keyframe_agent.output_dir / f"video-{video_id}"
            keyframe_dir = output_dir / "keyframes"
            metadata_path = output_dir / "metadata.json"

            result = ProcessingResult(
                video_id=video_id,
                video_path=video_path,
                total_frames=total_frames,
                total_detections=total_detections,
                keyframes_extracted=keyframes_extracted,
                processing_time_seconds=processing_time,
                output_dir=output_dir,
                keyframe_dir=keyframe_dir,
                metadata_path=metadata_path,
                keyframes=keyframe_dicts,
                started_at=started_at,
                completed_at=completed_at,
            )

            # Save comprehensive metadata
            self._save_metadata(result)

            if progress_callback:
                progress_callback(STAGE_COMPLETE, 100)

            logger.info(
                f"Video processing complete: video_id={video_id}, "
                f"detections={total_detections}, keyframes={keyframes_extracted}, "
                f"time={processing_time:.2f}s"
            )

            return result

        except FileNotFoundError:
            logger.error(f"Video file not found: {video_path}")
            raise

        except VideoProcessingError:
            logger.error(f"Video processing failed for {video_id}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error processing video {video_id}: {e}", exc_info=True)
            raise VideoProcessingError(f"Video processing failed: {e}") from e

    def _validate_video_path(self, video_path: Path) -> None:
        """
        Validate video file exists and is readable.

        Args:
            video_path: Path to video file

        Raises:
            FileNotFoundError: If video doesn't exist
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.debug(f"Video path validated: {video_path}")

    def _merge_config(self, custom_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge custom config with defaults.

        Custom config values override defaults.

        Args:
            custom_config: Optional custom configuration dict

        Returns:
            Merged configuration dict
        """
        if custom_config is None:
            return self.default_config.copy()

        # Merge: custom overrides defaults
        merged = self.default_config.copy()
        merged.update(custom_config)

        return merged

    def _get_total_frames(self, video_path: Path) -> int:
        """
        Get total frame count from video.

        Args:
            video_path: Path to video file

        Returns:
            Total number of frames

        Raises:
            VideoProcessingError: If video cannot be read
        """
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video file: {video_path}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            logger.debug(f"Video has {total_frames} frames")
            return total_frames

        finally:
            cap.release()

    def _save_metadata(self, result: ProcessingResult) -> None:
        """
        Save comprehensive metadata to JSON file.

        Saves all processing information including video stats, detections,
        keyframes, processing time, and timestamps.

        Args:
            result: ProcessingResult object with all metadata
        """
        metadata = {
            "video_id": result.video_id,
            "video_path": str(result.video_path),
            "total_frames": result.total_frames,
            "total_detections": result.total_detections,
            "keyframes_extracted": result.keyframes_extracted,
            "processing_time_seconds": result.processing_time_seconds,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "keyframes": result.keyframes,
        }

        # Ensure output directory exists
        result.output_dir.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        with open(result.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Comprehensive metadata saved to: {result.metadata_path}")

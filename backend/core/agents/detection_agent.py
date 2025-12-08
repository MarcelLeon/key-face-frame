"""
Detection Agent

YOLOv8-based person detection in video frames.
Optimized for Apple Silicon (M4) with MPS backend.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from backend.core.exceptions import VideoProcessingError

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single person detection result."""

    frame_index: int
    timestamp: float  # seconds
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    track_id: Optional[int] = None


class DetectionAgent:
    """
    Person detection agent using YOLOv8.

    Optimized for Apple Silicon (M4) with MPS backend.
    Supports streaming processing for memory efficiency.

    Attributes:
        model: YOLOv8 model instance
        confidence_threshold: Minimum detection confidence [0-1]
        device: Device to run inference on ('mps', 'cuda', 'cpu', or 'auto')

    Example:
        >>> agent = DetectionAgent(model_name="yolov8m.pt")
        >>> detections = await agent.process_video(video_path)
        >>> print(f"Found {len(detections)} person detections")
    """

    def __init__(
        self,
        model_name: str = "yolov8m.pt",
        confidence_threshold: float = 0.5,
        device: Optional[str] = None,
    ) -> None:
        """
        Initialize detection agent.

        Args:
            model_name: YOLO model variant (e.g., 'yolov8n.pt', 'yolov8m.pt')
            confidence_threshold: Minimum detection confidence [0-1]
            device: Force device ('mps', 'cpu', 'cuda') or None for auto-detect

        Raises:
            RuntimeError: If model cannot be loaded
        """
        self.confidence_threshold = confidence_threshold

        # Auto-detect device if not specified
        if device is None:
            self.device = self._auto_detect_device()
        else:
            self.device = device

        # Load YOLO model
        try:
            logger.info(f"Loading YOLO model: {model_name} on device: {self.device}")
            self.model = YOLO(model_name)

            # Move model to specified device if needed
            if self.device != "auto":
                self.model.to(self.device)

            logger.info(f"YOLO model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"Failed to load YOLO model {model_name}: {e}")

    def _auto_detect_device(self) -> str:
        """
        Auto-detect best available device.

        Prioritizes: MPS (Apple Silicon) > CUDA > CPU

        Returns:
            Device string ('mps', 'cuda', or 'cpu')
        """
        # Check for Apple Silicon MPS
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("MPS (Apple Silicon) detected")
            return "mps"

        # Check for NVIDIA CUDA
        if torch.cuda.is_available():
            logger.info("CUDA GPU detected")
            return "cuda"

        # Fallback to CPU
        logger.info("No GPU detected, using CPU")
        return "cpu"

    async def detect_persons_in_frame(
        self,
        frame: np.ndarray,
        frame_index: int = 0,
        fps: float = 30.0,
    ) -> List[Detection]:
        """
        Detect persons in a single frame.

        Args:
            frame: BGR image (H, W, 3) as numpy array
            frame_index: Frame number in video sequence
            fps: Frames per second (for timestamp calculation)

        Returns:
            List of Detection objects for persons found

        Raises:
            ValueError: If frame is invalid
        """
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame: frame is None or empty")

        # Run YOLO inference
        # classes=[0] means only detect person class
        # conf sets confidence threshold
        results = self.model(
            frame,
            classes=[0],  # Person class only
            conf=self.confidence_threshold,
            verbose=False,
        )

        # Parse detections
        detections: List[Detection] = []

        for result in results:
            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                # Extract bounding box coordinates [x1, y1, x2, y2]
                xyxy = box.xyxy[0].cpu().numpy()
                bbox = xyxy.tolist()

                # Extract confidence score
                conf = float(box.conf[0].cpu().numpy())

                # Filter by confidence threshold
                if conf < self.confidence_threshold:
                    continue

                # Extract track ID if available
                track_id = None
                if box.id is not None:
                    track_id = int(box.id[0].cpu().numpy())

                # Calculate timestamp
                timestamp = frame_index / fps if fps > 0 else 0.0

                detection = Detection(
                    frame_index=frame_index,
                    timestamp=timestamp,
                    bbox=bbox,
                    confidence=conf,
                    track_id=track_id,
                )

                detections.append(detection)

        logger.debug(f"Frame {frame_index}: detected {len(detections)} person(s)")

        return detections

    async def process_video(
        self,
        video_path: Path,
        sample_rate: int = 1,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Detection]:
        """
        Process entire video and detect persons.

        Uses streaming approach for memory efficiency - processes frames
        one at a time without loading entire video into memory.

        Args:
            video_path: Path to video file
            sample_rate: Process every Nth frame (1 = all frames)
            progress_callback: Optional callback(current_frame, total_frames)

        Returns:
            List of all detections across video

        Raises:
            VideoProcessingError: If video cannot be read or is invalid

        Example:
            >>> def on_progress(current, total):
            ...     print(f"Progress: {current}/{total}")
            >>> detections = await agent.process_video(
            ...     video_path,
            ...     sample_rate=2,
            ...     progress_callback=on_progress
            ... )
        """
        # Validate video path
        if not video_path.exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")

        # Open video capture
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise VideoProcessingError(
                f"Cannot open video file: {video_path}. "
                "File may be corrupted or format unsupported."
            )

        try:
            # Get video metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(
                f"Processing video: {video_path.name} "
                f"({total_frames} frames, {fps:.2f} FPS, sample_rate={sample_rate})"
            )

            # Handle empty video
            if total_frames == 0:
                logger.warning("Video has 0 frames")
                return []

            # Process frames with streaming approach
            all_detections: List[Detection] = []
            frame_index = 0

            while cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    # End of video
                    break

                # Sample frames based on sample_rate
                if frame_index % sample_rate == 0:
                    # Detect persons in this frame
                    detections = await self.detect_persons_in_frame(
                        frame,
                        frame_index=frame_index,
                        fps=fps,
                    )

                    all_detections.extend(detections)

                # Update progress
                if progress_callback is not None:
                    progress_callback(frame_index + 1, total_frames)

                frame_index += 1

            # Final progress update
            if progress_callback is not None:
                progress_callback(total_frames, total_frames)

            logger.info(
                f"Video processing complete: {len(all_detections)} detections "
                f"across {frame_index} frames"
            )

            return all_detections

        except Exception as e:
            logger.error(f"Error processing video {video_path}: {e}", exc_info=True)

            # Ensure we release resources even on error
            cap.release()

            # Re-raise as VideoProcessingError if not already
            if isinstance(e, VideoProcessingError):
                raise
            else:
                raise VideoProcessingError(f"Video processing failed: {e}") from e

        finally:
            # Always release video capture
            cap.release()
            logger.debug(f"Released video capture for {video_path.name}")

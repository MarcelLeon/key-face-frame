"""
Keyframe Agent

Intelligent keyframe selection and extraction from detected persons in video.
Implements multi-criteria scoring: person size, confidence, centrality, and track stability.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

import cv2
import numpy as np

from backend.core.exceptions import KeyframeExtractionError

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Keyframe:
    """Extracted keyframe metadata."""

    frame_index: int
    timestamp: float  # seconds
    score: float
    bbox: List[float]  # [x1, y1, x2, y2]
    filename: str
    track_id: Optional[int] = None


class KeyframeAgent:
    """
    Keyframe extraction agent.

    Extracts high-quality keyframes of detected persons from videos.
    Uses multi-criteria scoring: person size, detection confidence, centrality.
    Deduplicates temporally similar frames.

    Attributes:
        output_dir: Base directory for saving keyframes
        time_threshold: Minimum time (seconds) between keyframes
        jpeg_quality: JPEG compression quality [0-100]

    Scoring Algorithm:
        score = (
            size_score * 0.4 +       # Person bbox area / frame area
            confidence_score * 0.3 +  # Detection confidence
            centrality_score * 0.2 +  # Distance from center
            stability_score * 0.1     # Track length (if available)
        )

    Example:
        >>> agent = KeyframeAgent(output_dir=Path("output"))
        >>> keyframes = await agent.extract_keyframes(
        ...     video_path=Path("video.mp4"),
        ...     detections=detections,
        ...     video_id="video-123",
        ...     max_frames=100
        ... )
        >>> print(f"Extracted {len(keyframes)} keyframes")
    """

    # Scoring weights (must sum to 1.0)
    WEIGHT_SIZE = 0.4
    WEIGHT_CONFIDENCE = 0.3
    WEIGHT_CENTRALITY = 0.2
    WEIGHT_STABILITY = 0.1

    def __init__(
        self,
        output_dir: Path,
        time_threshold: float = 1.0,
        jpeg_quality: int = 95,
    ) -> None:
        """
        Initialize keyframe agent.

        Args:
            output_dir: Base directory for saving keyframes
            time_threshold: Min time (seconds) between keyframes
            jpeg_quality: JPEG compression quality [0-100]
        """
        self.output_dir = output_dir
        self.time_threshold = time_threshold
        self.jpeg_quality = jpeg_quality

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"KeyframeAgent initialized: output_dir={output_dir}, "
            f"time_threshold={time_threshold}s, jpeg_quality={jpeg_quality}"
        )

    async def extract_keyframes(
        self,
        video_path: Path,
        detections: List[Dict],
        video_id: str,
        max_frames: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Keyframe]:
        """
        Extract keyframes from video based on detections.

        Args:
            video_path: Path to source video
            detections: List of Detection dicts from DetectionAgent
            video_id: Unique identifier for this video
            max_frames: Maximum keyframes to extract
            progress_callback: Optional callback(current, total)

        Returns:
            List of Keyframe objects with metadata

        Raises:
            KeyframeExtractionError: If extraction fails
        """
        logger.info(
            f"Starting keyframe extraction: video_id={video_id}, "
            f"detections={len(detections)}, max_frames={max_frames}"
        )

        # Validate video path
        if not video_path.exists():
            raise KeyframeExtractionError(f"Video file not found: {video_path}")

        # Get video dimensions
        try:
            video_width, video_height = self._get_video_dimensions(video_path)
        except Exception as e:
            raise KeyframeExtractionError(f"Failed to read video: {e}") from e

        # 1. Collect candidate frames
        candidates = self._collect_candidates(detections)
        logger.debug(f"Collected {len(candidates)} candidate frames")

        if not candidates:
            logger.warning("No candidates found, returning empty list")
            return []

        # 2. Score frames by multiple criteria
        scored = self._score_frames(candidates, video_width, video_height)
        logger.debug(f"Scored {len(scored)} frames")

        # 3. Remove temporally close duplicates
        unique = self._remove_duplicates(scored)
        logger.debug(f"After deduplication: {len(unique)} unique frames")

        # 4. Select top N frames
        selected = sorted(unique, key=lambda x: x["score"], reverse=True)[:max_frames]
        logger.info(f"Selected {len(selected)} keyframes for extraction")

        # 5. Extract and save frames
        keyframes = await self._save_keyframes(
            video_path=video_path,
            frames=selected,
            video_id=video_id,
            progress_callback=progress_callback,
        )

        # 6. Save metadata
        await self._save_metadata(keyframes, video_id, max_frames, video_path)

        logger.info(f"Keyframe extraction complete: {len(keyframes)} frames saved")
        return keyframes

    def _get_video_dimensions(self, video_path: Path) -> tuple[int, int]:
        """
        Get video width and height.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (width, height)

        Raises:
            KeyframeExtractionError: If video cannot be read
        """
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise KeyframeExtractionError(f"Cannot open video: {video_path}")

        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if width == 0 or height == 0:
                raise KeyframeExtractionError("Invalid video dimensions")

            return width, height

        finally:
            cap.release()

    def _collect_candidates(self, detections: List[Dict]) -> List[Dict]:
        """
        Collect candidate frames from detections.

        Args:
            detections: List of detection dicts

        Returns:
            List of candidate frame dicts
        """
        candidates = []

        for detection in detections:
            candidate = {
                "frame_index": detection["frame_index"],
                "timestamp": detection["timestamp"],
                "bbox": detection["bbox"],
                "confidence": detection.get("confidence", 0.0),
                "track_id": detection.get("track_id"),
            }
            candidates.append(candidate)

        return candidates

    def _score_frames(
        self, candidates: List[Dict], video_width: int, video_height: int
    ) -> List[Dict]:
        """
        Score candidate frames by multiple criteria.

        Scoring criteria:
        1. Person size (bbox area relative to frame)
        2. Detection confidence
        3. Centrality (person near frame center)
        4. Track stability (if track_id available)

        Args:
            candidates: List of candidate frames
            video_width: Video frame width
            video_height: Video frame height

        Returns:
            List of scored frames (sorted by score descending)
        """
        frame_area = video_width * video_height
        frame_center_x = video_width / 2
        frame_center_y = video_height / 2

        # Calculate maximum possible distance from center (diagonal)
        max_distance = np.sqrt((video_width / 2) ** 2 + (video_height / 2) ** 2)

        for candidate in candidates:
            bbox = candidate["bbox"]
            x1, y1, x2, y2 = bbox

            # 1. Size score (normalized bbox area)
            bbox_area = (x2 - x1) * (y2 - y1)
            size_score = min(1.0, bbox_area / frame_area * 10)  # Scale up small persons

            # 2. Confidence score (already normalized 0-1)
            confidence_score = candidate.get("confidence", 0.0)

            # 3. Centrality score (distance from center, inverted)
            person_center_x = (x1 + x2) / 2
            person_center_y = (y1 + y2) / 2
            distance = np.sqrt(
                (person_center_x - frame_center_x) ** 2 + (person_center_y - frame_center_y) ** 2
            )
            centrality_score = 1.0 - (distance / max_distance)

            # 4. Stability score (placeholder - would need track analysis)
            # For now, just give small bonus if track_id exists
            stability_score = 0.5 if candidate.get("track_id") is not None else 0.0

            # Weighted sum
            total_score = (
                size_score * self.WEIGHT_SIZE
                + confidence_score * self.WEIGHT_CONFIDENCE
                + centrality_score * self.WEIGHT_CENTRALITY
                + stability_score * self.WEIGHT_STABILITY
            )

            candidate["score"] = total_score

        # Sort by score descending
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _remove_duplicates(self, frames: List[Dict]) -> List[Dict]:
        """
        Remove temporally similar frames, keeping highest scored.

        Args:
            frames: List of scored frames

        Returns:
            List of unique frames
        """
        if not frames:
            return []

        # Sort by timestamp
        sorted_frames = sorted(frames, key=lambda x: x["timestamp"])

        # Group frames within time_threshold and keep best
        unique = []
        current_group = [sorted_frames[0]]

        for frame in sorted_frames[1:]:
            time_diff = frame["timestamp"] - current_group[0]["timestamp"]

            if time_diff < self.time_threshold:
                # Within threshold, add to current group
                current_group.append(frame)
            else:
                # Beyond threshold, save best from current group and start new
                best = max(current_group, key=lambda x: x["score"])
                unique.append(best)
                current_group = [frame]

        # Don't forget the last group
        if current_group:
            best = max(current_group, key=lambda x: x["score"])
            unique.append(best)

        return unique

    async def _save_keyframes(
        self,
        video_path: Path,
        frames: List[Dict],
        video_id: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Keyframe]:
        """
        Extract and save selected frames as JPEGs.

        Args:
            video_path: Path to source video
            frames: List of frame dicts to extract
            video_id: Video identifier
            progress_callback: Optional progress callback

        Returns:
            List of saved Keyframe objects

        Raises:
            KeyframeExtractionError: If saving fails
        """
        # Create output directory structure
        video_output_dir = self.output_dir / f"video-{video_id}"
        keyframes_dir = video_output_dir / "keyframes"
        keyframes_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Saving keyframes to: {keyframes_dir}")

        # Open video
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise KeyframeExtractionError(f"Cannot open video: {video_path}")

        try:
            keyframes = []
            total = len(frames)

            for idx, frame_data in enumerate(frames):
                keyframe = await self._save_single_frame(
                    video_path=video_path,
                    frame_data=frame_data,
                    output_path=keyframes_dir,
                )
                keyframes.append(keyframe)

                # Progress callback
                if progress_callback is not None:
                    progress_callback(idx + 1, total)

            return keyframes

        finally:
            cap.release()

    async def _save_single_frame(
        self,
        video_path: Path,
        frame_data: Dict,
        output_path: Path,
    ) -> Keyframe:
        """
        Save a single frame as JPEG.

        Args:
            video_path: Path to video file
            frame_data: Frame metadata dict
            output_path: Directory to save frame

        Returns:
            Keyframe object

        Raises:
            KeyframeExtractionError: If frame cannot be saved
        """
        frame_index = frame_data["frame_index"]
        timestamp = frame_data["timestamp"]

        # Open video and seek to frame
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise KeyframeExtractionError(f"Cannot open video: {video_path}")

        try:
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()

            if not ret or frame is None:
                raise KeyframeExtractionError(f"Failed to read frame {frame_index} from video")

            # Generate filename: frame_{index:05d}_t{timestamp:.2f}s.jpg
            filename = f"frame_{frame_index:05d}_t{timestamp:.2f}s.jpg"
            output_file = output_path / filename

            # Save as JPEG
            success = cv2.imwrite(
                str(output_file), frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            )

            if not success:
                raise KeyframeExtractionError(f"Failed to write frame to {output_file}")

            logger.debug(f"Saved keyframe: {filename}")

            # Create Keyframe object
            keyframe = Keyframe(
                frame_index=frame_index,
                timestamp=timestamp,
                score=frame_data["score"],
                bbox=frame_data["bbox"],
                filename=filename,
                track_id=frame_data.get("track_id"),
            )

            return keyframe

        finally:
            cap.release()

    async def _save_metadata(
        self,
        keyframes: List[Keyframe],
        video_id: str,
        max_frames: int,
        video_path: Path,
    ) -> None:
        """
        Save keyframes metadata to JSON file.

        Args:
            keyframes: List of Keyframe objects
            video_id: Video identifier
            max_frames: Max frames parameter used
            video_path: Path to source video file
        """
        video_output_dir = self.output_dir / f"video-{video_id}"
        metadata_path = video_output_dir / "metadata.json"

        metadata = {
            "video_id": video_id,
            "video_path": str(video_path),
            "total_keyframes": len(keyframes),
            "extraction_params": {
                "max_frames": max_frames,
                "time_threshold": self.time_threshold,
                "jpeg_quality": self.jpeg_quality,
            },
            "keyframes": [asdict(kf) for kf in keyframes],
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Metadata saved to: {metadata_path}")

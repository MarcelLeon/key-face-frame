"""
Custom Exceptions

Application-specific exception classes.
"""


class VideoProcessingError(Exception):
    """Base exception for video processing errors."""

    pass


class VideoFormatError(VideoProcessingError):
    """Video format not supported or invalid."""

    pass


class VideoTooLargeError(VideoProcessingError):
    """Video file exceeds size limit."""

    pass


class KeyframeExtractionError(VideoProcessingError):
    """Keyframe extraction failed."""

    pass

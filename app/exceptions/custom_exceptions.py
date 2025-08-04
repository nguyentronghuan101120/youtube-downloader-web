import logging

logger = logging.getLogger(__name__)


class VideoDownloadException(Exception):
    """Custom exception for video download errors"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(f"[VideoDownloadException] - {message}")


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(f"[ValidationError] - {message}")


class FFmpegNotFoundError(Exception):
    """Custom exception for FFmpeg not found"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(f"[FFmpegNotFoundError] - {message}")


class NetworkError(Exception):
    """Custom exception for network-related errors"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(f"[NetworkError] - {message}") 
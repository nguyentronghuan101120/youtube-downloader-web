import re
import logging
from typing import Optional
from config import CONFIG
from app.exceptions.custom_exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube URL"""
    logger.debug(f"[validate_youtube_url] - Validating URL: {url}")

    youtube_patterns = [
        r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+",
        r"https?://youtu\.be/[\w-]+",
        r"https?://(?:www\.)?youtube\.com/embed/[\w-]+",
    ]

    is_valid = any(re.match(pattern, url) for pattern in youtube_patterns)
    logger.debug(f"[validate_youtube_url] - URL validation result: {is_valid}")

    return is_valid


def validate_format_type(format_type: str) -> bool:
    """Validate if the format type is supported"""
    if format_type not in CONFIG["supported_formats"]:
        logger.error(f"[validate_format_type] - Unsupported format: {format_type}")
        return False
    return True


def validate_audio_format(audio_format: str) -> bool:
    """Validate if the audio format is supported"""
    if audio_format not in CONFIG["supported_audio_formats"]:
        logger.error(f"[validate_audio_format] - Unsupported audio format: {audio_format}")
        return False
    return True


def validate_video_quality(video_quality: str) -> bool:
    """Validate if the video quality is supported"""
    if video_quality not in CONFIG["video_qualities"]:
        logger.error(f"[validate_video_quality] - Unsupported video quality: {video_quality}")
        return False
    return True


def validate_download_parameters(
    format_type: str,
    audio_format: Optional[str] = None,
    video_quality: Optional[str] = None
) -> None:
    """Validate all download parameters"""
    if not validate_format_type(format_type):
        raise ValidationError(f"Unsupported format type: {format_type}")
    
    if format_type == "audio" and audio_format:
        if not validate_audio_format(audio_format):
            raise ValidationError(f"Unsupported audio format: {audio_format}")
    
    if format_type == "video" and video_quality:
        if not validate_video_quality(video_quality):
            raise ValidationError(f"Unsupported video quality: {video_quality}")


def validate_video_info(video_info: dict) -> bool:
    """Validate video information structure"""
    required_fields = ["id", "title", "url"]
    
    for field in required_fields:
        if field not in video_info:
            logger.error(f"[validate_video_info] - Missing required field: {field}")
            return False
    
    return True


def validate_playlist_info(playlist_info: dict) -> bool:
    """Validate playlist information structure"""
    required_fields = ["type", "title", "videos"]
    
    for field in required_fields:
        if field not in playlist_info:
            logger.error(f"[validate_playlist_info] - Missing required field: {field}")
            return False
    
    if playlist_info["type"] != "playlist":
        logger.error(f"[validate_playlist_info] - Invalid type: {playlist_info['type']}")
        return False
    
    if not isinstance(playlist_info["videos"], list):
        logger.error(f"[validate_playlist_info] - Videos must be a list")
        return False
    
    return True 
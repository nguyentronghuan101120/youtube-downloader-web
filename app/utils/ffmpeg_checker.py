import os
import subprocess
import logging
from app.exceptions.custom_exceptions import FFmpegNotFoundError

logger = logging.getLogger(__name__)


def check_ffmpeg_availability():
    """Check if FFmpeg is available"""

    try:
        # Check if FFmpeg environment variables are set (from bundled FFmpeg)
        ffmpeg_binary = os.environ.get("FFMPEG_BINARY")
        ffprobe_binary = os.environ.get("FFPROBE_BINARY")

        logger.debug(
            f"[check_ffmpeg_availability] - FFMPEG_BINARY env: {ffmpeg_binary}"
        )
        logger.debug(
            f"[check_ffmpeg_availability] - FFPROBE_BINARY env: {ffprobe_binary}"
        )

        if ffmpeg_binary and os.path.exists(ffmpeg_binary):
            logger.info(
                f"[check_ffmpeg_availability] - Found FFmpeg binary at: {ffmpeg_binary}"
            )
            return True
        elif ffprobe_binary and os.path.exists(ffprobe_binary):
            logger.info(
                f"[check_ffmpeg_availability] - Found FFprobe binary at: {ffprobe_binary}"
            )
            return True

        # Check if FFmpeg is in PATH
        logger.debug("[check_ffmpeg_availability] - Checking FFmpeg in PATH")
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True

        # Check if ffprobe is in PATH
        logger.debug("[check_ffmpeg_availability] - Checking FFprobe in PATH")
        result = subprocess.run(
            ["ffprobe", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            logger.info("[check_ffmpeg_availability] - FFprobe found in PATH")
            return True

        # Try to find FFmpeg using which command
        try:
            logger.debug(
                "[check_ffmpeg_availability] - Using 'which' command to locate FFmpeg"
            )
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                ffmpeg_path = result.stdout.strip()
                logger.info(
                    f"[check_ffmpeg_availability] - FFmpeg found via 'which': {ffmpeg_path}"
                )
                return True
        except Exception as e:
            logger.debug(
                f"[check_ffmpeg_availability] - 'which' command failed: {str(e)}"
            )

        logger.warning("[check_ffmpeg_availability] - FFmpeg not found anywhere")
        return False

    except Exception as e:
        logger.error(
            f"[check_ffmpeg_availability] - Error during FFmpeg check: {str(e)}"
        )
        return False


def get_ffmpeg_path():
    """Get FFmpeg path from environment or system"""
    ffmpeg_binary = os.environ.get("FFMPEG_BINARY")
    ffprobe_binary = os.environ.get("FFPROBE_BINARY")
    
    if ffmpeg_binary and os.path.exists(ffmpeg_binary):
        return os.path.dirname(ffmpeg_binary)
    elif ffprobe_binary and os.path.exists(ffprobe_binary):
        return os.path.dirname(ffprobe_binary)
    
    # Try to find FFmpeg using which command
    try:
        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.strip()
            return os.path.dirname(ffmpeg_path)
    except Exception:
        pass
    
    return None


def setup_ffmpeg_env():
    """Setup FFmpeg environment variables"""
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        os.environ["FFMPEG_BINARY"] = os.path.join(ffmpeg_path, "ffmpeg")
        os.environ["FFPROBE_BINARY"] = os.path.join(ffmpeg_path, "ffprobe")
        return True
    return False 
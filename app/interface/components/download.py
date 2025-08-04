import os
import multiprocessing
import logging
from typing import Optional, List, Tuple
from config import CONFIG
from app.core.downloader import download_single_video, download_multiple_videos
from app.core.video_info import get_video_info
from app.core.validators import validate_youtube_url
from app.core.progress_tracker import clear_progress
from app.utils.file_manager import get_downloads_directory

logger = logging.getLogger(__name__)


def get_download_placeholder_html() -> str:
    """
    Generates a placeholder HTML for the download content section.
    """
    return """
    <div style="
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        text-align: center;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px dashed #ccc;
        color: #888;
    ">
        <p style="font-size: 1em; font-weight: 500; margin: 0;">Download status will appear here after a successful download.</p>
    </div>
    """


def download_content(
    url: str,
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
    selected_videos: List[int] = None,
) -> Tuple[Optional[str], str]:
    """
    Download video(s) based on user selection

    Returns:
        (file_path, status_message)
    """
    if not url.strip():
        return None, "❌ Please enter a YouTube URL"

    if not validate_youtube_url(url):
        return None, "❌ Invalid YouTube URL"

    try:
        # Clear previous progress
        clear_progress()

        # Validate and set default values based on format type
        if format_type == "video":
            video_quality = video_quality or "1080p"
            audio_format = None  # Not used for video downloads
        elif format_type == "audio":
            audio_format = audio_format or CONFIG["default_audio_format"]
            video_quality = None  # Not used for audio downloads
        else:
            return None, f"❌ Invalid format type: {format_type}"

        # Create downloads directory in current working directory
        downloads_dir = get_downloads_directory()

        info = get_video_info(url)

        if info.get("type") == "playlist":
            videos = info.get("videos", [])

            # Filter selected videos if specified
            if selected_videos:
                videos = [videos[i] for i in selected_videos if i < len(videos)]

            if not videos:
                return None, "❌ No videos selected or found"

            if len(videos) == 1:
                # Single video from playlist
                file_path = download_single_video(
                    videos[0],
                    format_type,
                    audio_format,
                    video_quality,
                    output_dir=downloads_dir,
                )
            else:
                # Multiple videos - create ZIP with parallel downloads using all CPU cores
                file_path = download_multiple_videos(
                    videos,
                    format_type,
                    audio_format,
                    video_quality,
                    max_workers=None,  # Auto-detect and use all CPU cores
                    output_dir=downloads_dir,  # Save ZIP to downloads directory
                )

            count = len(videos)
            if count > 1:
                cpu_cores = multiprocessing.cpu_count()
                success_msg = f"✅ Successfully downloaded {count} videos using parallel processing ({cpu_cores} CPU cores utilized)"
            else:
                success_msg = f"✅ Successfully downloaded {count} video"
            return (
                file_path,
                success_msg,
            )

        else:
            # Single video
            file_path = download_single_video(
                info,
                format_type,
                audio_format,
                video_quality,
                output_dir=downloads_dir,
            )
            return file_path, "✅ Successfully downloaded video"

    except Exception as e:
        return None, f"❌ Download error: {str(e)}"


def handle_single_video(
    video_info: dict,
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
) -> Tuple[Optional[str], str]:
    """Handle download of a single video"""
    try:
        downloads_dir = get_downloads_directory()
        file_path = download_single_video(
            video_info,
            format_type,
            audio_format,
            video_quality,
            output_dir=downloads_dir,
        )
        return file_path, "✅ Successfully downloaded video"
    except Exception as e:
        return None, f"❌ Download error: {str(e)}"


def handle_playlist(
    playlist_info: dict,
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
    selected_videos: List[int],
) -> Tuple[Optional[str], str]:
    """Handle download of a playlist"""
    try:
        videos = playlist_info.get("videos", [])

        # Filter selected videos if specified
        if selected_videos:
            videos = [videos[i] for i in selected_videos if i < len(videos)]

        if not videos:
            return None, "❌ No videos selected or found"

        downloads_dir = get_downloads_directory()

        if len(videos) == 1:
            # Single video from playlist
            file_path = download_single_video(
                videos[0],
                format_type,
                audio_format,
                video_quality,
                output_dir=downloads_dir,
            )
        else:
            # Multiple videos - create ZIP with parallel downloads
            file_path = download_multiple_videos(
                videos,
                format_type,
                audio_format,
                video_quality,
                max_workers=None,  # Auto-detect and use all CPU cores
                output_dir=downloads_dir,
            )

        count = len(videos)
        if count > 1:
            cpu_cores = multiprocessing.cpu_count()
            success_msg = f"✅ Successfully downloaded {count} videos using parallel processing ({cpu_cores} CPU cores utilized)"
        else:
            success_msg = f"✅ Successfully downloaded {count} video"
        
        return file_path, success_msg

    except Exception as e:
        return None, f"❌ Download error: {str(e)}"


def validate_download_request(
    url: str,
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
) -> Tuple[bool, str]:
    """Validate download request parameters"""
    if not url.strip():
        return False, "❌ Please enter a YouTube URL"

    if not validate_youtube_url(url):
        return False, "❌ Invalid YouTube URL"

    if format_type not in CONFIG["supported_formats"]:
        return False, f"❌ Invalid format type: {format_type}"

    if format_type == "audio" and audio_format not in CONFIG["supported_audio_formats"]:
        return False, f"❌ Invalid audio format: {audio_format}"

    if format_type == "video" and video_quality not in CONFIG["video_qualities"]:
        return False, f"❌ Invalid video quality: {video_quality}"

    return True, "" 
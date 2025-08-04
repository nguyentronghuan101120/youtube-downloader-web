import os
import tempfile
import shutil
import zipfile
import logging
import datetime
import multiprocessing
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Union

import yt_dlp
from yt_dlp.utils import sanitize_filename

from config import CONFIG
from app.exceptions.custom_exceptions import VideoDownloadException
from app.core.video_info import get_video_info
from app.core.progress_tracker import (
    ProgressTracker,
    update_progress,
    update_overall_progress,
)
from app.utils.ffmpeg_checker import check_ffmpeg_availability, get_ffmpeg_path
from app.utils.file_manager import (
    ensure_directory_exists,
    cleanup_temp_files,
    create_zip_file,
    find_downloaded_files,
    get_downloads_directory,
)
from app.core.validators import validate_download_parameters

logger = logging.getLogger(__name__)


def get_download_options(
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
    output_template: str,
    progress_hook=None,
) -> Dict:
    """Get yt-dlp download options based on format settings"""

    if format_type not in CONFIG["supported_formats"]:
        error_msg = f"Unsupported format: {format_type}"
        logger.error(f"[get_download_options] - {error_msg}")
        raise ValueError(error_msg)

    if format_type == "audio" and (
        audio_format is None or audio_format not in CONFIG["supported_audio_formats"]
    ):
        error_msg = f"Unsupported audio format: {audio_format}"
        logger.error(f"[get_download_options] - {error_msg}")
        raise ValueError(error_msg)

    base_options = {
        "outtmpl": output_template,
        "quiet": True,
        "embedthumbnail": True,
        "nooverwrites": True,
        "noprogress": True,
    }

    if progress_hook:
        base_options["progress_hooks"] = [progress_hook]
        logger.debug("[get_download_options] - Progress hook attached")

    # Add FFmpeg location if available from environment
    ffmpeg_binary = os.environ.get("FFMPEG_BINARY")
    ffprobe_binary = os.environ.get("FFPROBE_BINARY")

    logger.debug(
        f"[get_download_options] - Checking FFmpeg paths: binary={ffmpeg_binary}, probe={ffprobe_binary}"
    )

    if ffmpeg_binary and os.path.exists(ffmpeg_binary):
        ffmpeg_dir = os.path.dirname(ffmpeg_binary)
        base_options["ffmpeg_location"] = ffmpeg_dir
        logger.info(
            f"[get_download_options] - FFmpeg location set from env: {ffmpeg_dir}"
        )
    elif ffprobe_binary and os.path.exists(ffprobe_binary):
        ffmpeg_dir = os.path.dirname(ffprobe_binary)
        base_options["ffmpeg_location"] = ffmpeg_dir
        logger.info(
            f"[get_download_options] - FFmpeg location set from probe env: {ffmpeg_dir}"
        )
    else:
        # Try to find FFmpeg in PATH
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
            if result.returncode == 0:
                ffmpeg_path = result.stdout.strip()
                ffmpeg_dir = os.path.dirname(ffmpeg_path)
                base_options["ffmpeg_location"] = ffmpeg_dir
        except Exception as e:
            logger.debug(
                f"[get_download_options] - Could not locate FFmpeg via PATH: {str(e)}"
            )

    if format_type == "video":
        # Handle None or default video quality
        if video_quality is None or video_quality == "best":
            format_str = "bestvideo+bestaudio"
        else:
            format_str = (
                f"bestvideo[height<={int(video_quality.replace('p', ''))}]+bestaudio"
            )
        base_options.update(
            {
                "format": format_str,
                "merge_output_format": "mkv",
            }
        )
        logger.info(f"[get_download_options] - Video format configured: {format_str}")

    elif format_type == "audio":
        base_options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format,
                        "preferredquality": "0",
                    }
                ],
                "extractaudio": True,
                "audioformat": audio_format,
            }
        )
        logger.info(f"[get_download_options] - Audio format configured: {audio_format}")

    logger.debug(f"[get_download_options] - Final options: {base_options}")
    return base_options


def download_single_video(
    video_url: Union[str, Dict],
    format_type: str = "video",
    audio_format: Optional[str] = "mp3",
    video_quality: Optional[str] = "1080p",
    output_dir: Optional[str] = None,
    progress_callback=None,
) -> str:
    """
    Download a single video

    Returns:
        Path to downloaded file
    """
    logger.info(
        f"[download_single_video] - Starting download: format={format_type}, quality={video_quality}"
    )

    # Validate and set default values based on format type
    if format_type == "video":
        video_quality = video_quality or "1080p"
        audio_format = audio_format or "mp3"  # Default for video downloads
    elif format_type == "audio":
        audio_format = audio_format or CONFIG["default_audio_format"]
        video_quality = video_quality or "720p"  # Default, but not used for audio

    logger.info(
        f"[download_single_video] - Validated parameters: format={format_type}, audio={audio_format}, quality={video_quality}"
    )

    if not check_ffmpeg_availability():
        error_msg = (
            "FFmpeg not found. This app requires FFmpeg for audio/video processing."
        )
        logger.error(f"[download_single_video] - {error_msg}")
        raise VideoDownloadException(error_msg)

    # Create temp directory if no output_dir specified
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    ensure_directory_exists(output_dir)

    try:
        # Get video info
        if isinstance(video_url, dict):
            logger.debug("[download_single_video] - Input is dict (video info)")
            info = video_url
            video_url = info["url"]
        else:
            logger.debug("[download_single_video] - Input is URL, getting info")
            info = get_video_info(video_url)
            if info.get("type") == "playlist":
                error_msg = "Expected single video, got playlist"
                logger.error(f"[download_single_video] - {error_msg}")
                raise VideoDownloadException(error_msg)

        video_id = info.get("id", "")
        video_title = sanitize_filename(info.get("title", "video"))
        output_template = os.path.join(output_dir, f"{video_title}")

        logger.info(
            f"[download_single_video] - Video details: ID={video_id}, Title={video_title}"
        )
        logger.debug(f"[download_single_video] - Output template: {output_template}")

        # Set up progress tracking
        progress_tracker = ProgressTracker()
        progress_hook = progress_tracker.get_hook(video_id, progress_callback)

        # Get download options
        ydl_opts = get_download_options(
            format_type, audio_format, video_quality, output_template, progress_hook
        )

        logger.info("[download_single_video] - Starting yt-dlp download")
        start_time = datetime.datetime.now()

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(
            f"[download_single_video] - Download completed in {duration:.2f} seconds"
        )

        # Find the downloaded file
        logger.debug("[download_single_video] - Searching for downloaded files")
        downloaded_files = find_downloaded_files(output_dir, video_title)

        if not downloaded_files:
            error_msg = "No file was downloaded"
            logger.error(f"[download_single_video] - {error_msg}")
            raise VideoDownloadException(error_msg)

        # Return path to the downloaded file
        result_path = os.path.join(output_dir, downloaded_files[0])
        file_size = os.path.getsize(result_path) if os.path.exists(result_path) else 0
        logger.info(
            f"[download_single_video] - Successfully downloaded: {result_path} ({file_size} bytes)"
        )

        return result_path

    except Exception as e:
        error_msg = f"Error downloading {video_url}: {str(e)}"
        logger.error(f"[download_single_video] - {error_msg}")
        raise VideoDownloadException(error_msg)


def download_multiple_videos(
    video_list: List[Dict],
    format_type: str = "video",
    audio_format: Optional[str] = "mp3",
    video_quality: Optional[str] = "720p",
    progress_callback=None,
    max_workers: int = None,  # Will auto-detect CPU cores if None
    output_dir: str = None,  # Output directory for the ZIP file
) -> str:
    """
    Download multiple videos in parallel and return path to ZIP file

    Args:
        video_list: List of video dictionaries
        format_type: 'video' or 'audio'
        audio_format: Audio format for audio downloads
        video_quality: Video quality for video downloads
        progress_callback: Progress update callback
        max_workers: Maximum number of concurrent downloads (None = auto-detect CPU cores)
        output_dir: Output directory for the ZIP file (None = current working directory + downloads)

    Returns:
        Path to ZIP file containing all downloads
    """

    # Auto-detect optimal number of workers based on CPU cores
    if max_workers is None:
        cpu_cores = multiprocessing.cpu_count()
        max_workers = cpu_cores  # Use all available CPU cores
        logger.info(
            f"[download_multiple_videos] - Auto-detected {cpu_cores} CPU cores, using {max_workers} workers"
        )
    else:
        logger.info(
            f"[download_multiple_videos] - Using specified {max_workers} workers"
        )

    # Set up output directory for final ZIP file
    if output_dir is None:
        output_dir = get_downloads_directory()
    ensure_directory_exists(output_dir)

    # Validate and set default values based on format type
    if format_type == "video":
        video_quality = video_quality or "1080p"
        audio_format = audio_format or "mp3"  # Default for video downloads
    elif format_type == "audio":
        audio_format = audio_format or CONFIG["default_audio_format"]
        video_quality = video_quality or "720p"  # Default, but not used for audio

    logger.info(
        f"[download_multiple_videos] - Validated parameters: format={format_type}, audio={audio_format}, quality={video_quality}, max_workers={max_workers}"
    )

    if not video_list:
        error_msg = "No videos to download"
        logger.error(f"[download_multiple_videos] - {error_msg}")
        raise VideoDownloadException(error_msg)

    # Create temporary directory for individual downloads
    temp_dir = tempfile.mkdtemp()

    # Generate unique ZIP filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    playlist_name = f"playlist_{timestamp}"
    zip_filename = f"{playlist_name}.zip"
    zip_path = os.path.join(output_dir, zip_filename)

    logger.info(f"[download_multiple_videos] - Created temp directory: {temp_dir}")
    logger.info(
        f"[download_multiple_videos] - Final ZIP file will be saved to: {zip_path}"
    )

    # Thread-safe progress tracking
    import threading

    progress_lock = threading.Lock()
    completed_count = 0
    total_videos = len(video_list)

    def download_single_with_progress(video_info):
        """Download a single video and update progress safely"""
        nonlocal completed_count

        video_title = video_info.get(
            "title", f"Video_{video_info.get('id', 'Unknown')}"
        )
        logger.info(f"[download_multiple_videos] - Starting download: {video_title}")

        try:
            file_path = download_single_video(
                video_info,
                format_type,
                audio_format,
                video_quality,
                temp_dir,
                progress_callback,
            )

            # Thread-safe progress update
            with progress_lock:
                completed_count += 1
                update_overall_progress(
                    completed_count, total_videos, video_title, progress_callback
                )

            logger.info(
                f"[download_multiple_videos] - Successfully downloaded: {video_title}"
            )
            return file_path, None

        except Exception as e:
            error_msg = f"Error downloading {video_title}: {str(e)}"
            logger.error(f"[download_multiple_videos] - {error_msg}")
            return None, error_msg

    try:
        downloaded_files = []
        errors = []
        start_time = datetime.datetime.now()

        # Use ThreadPoolExecutor for parallel downloads
        logger.info(
            f"[download_multiple_videos] - Starting parallel downloads with {max_workers} workers"
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_video = {
                executor.submit(download_single_with_progress, video): video
                for video in video_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    file_path, error = future.result()
                    if file_path:
                        downloaded_files.append(file_path)
                    if error:
                        errors.append(error)
                except Exception as e:
                    error_msg = f"Unexpected error for {video.get('title', 'Unknown')}: {str(e)}"
                    logger.error(f"[download_multiple_videos] - {error_msg}")
                    errors.append(error_msg)

        if not downloaded_files:
            error_msg = "No videos were successfully downloaded"
            if errors:
                error_msg += f". Errors: {'; '.join(errors[:3])}"  # Show first 3 errors
            logger.error(f"[download_multiple_videos] - {error_msg}")
            raise VideoDownloadException(error_msg)

        logger.info(
            f"[download_multiple_videos] - Creating ZIP with {len(downloaded_files)} files"
        )
        if errors:
            logger.warning(
                f"[download_multiple_videos] - {len(errors)} videos failed to download"
            )

        # Create ZIP file
        create_zip_file(downloaded_files, zip_path)

        end_time = datetime.datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        zip_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0

        logger.info(
            f"[download_multiple_videos] - Parallel download completed in {total_duration:.2f} seconds"
        )
        logger.info(
            f"[download_multiple_videos] - ZIP file saved to: {zip_path} ({zip_size} bytes)"
        )
        logger.info(
            f"[download_multiple_videos] - Success rate: {len(downloaded_files)}/{total_videos} videos"
        )

        # Clean up temporary directory (but keep the final ZIP file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(
                f"[download_multiple_videos] - Cleaned up temp directory: {temp_dir}"
            )

        return zip_path

    except Exception as e:
        # Cleanup on error
        logger.error(f"[download_multiple_videos] - Error in batch download: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(
                f"[download_multiple_videos] - Cleaned up temp directory: {temp_dir}"
            )

        error_msg = f"Error in batch download: {str(e)}"
        raise VideoDownloadException(error_msg)

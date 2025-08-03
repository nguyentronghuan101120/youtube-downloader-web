import json
import os
import subprocess
import tempfile
import shutil
import zipfile
import logging
import datetime
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
import sys
import re
from typing import Dict, List, Optional, Union

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(message)s\n",
    handlers=[
        logging.FileHandler("youtube_downloader.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

try:
    import yt_dlp
    from yt_dlp.utils import sanitize_filename

except ImportError:
    logger.warning("[IMPORT] - yt_dlp not found. Installing it now...")
    print("yt_dlp not found. Installing it now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
    from yt_dlp.utils import sanitize_filename

    logger.info("[IMPORT] - yt_dlp installed and imported successfully")

# Config
CONFIG = {
    "max_workers": 4,
    "supported_formats": ["video", "audio"],
    "supported_audio_formats": ["mp3", "m4a", "wav", "flac", "aac"],
    "default_audio_format": "mp3",
    "default_video_quality": "720p",
    "video_qualities": [
        "240p",
        "360p",
        "480p",
        "720p",
        "1080p",
        "1440p",
        "2160p",
        "best",
    ],
}


class VideoDownloadException(Exception):
    """Custom exception for video download errors"""

    def __init__(self, message):
        super().__init__(message)
        logger.error(f"[VideoDownloadException] - {message}")


def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    logger.debug(f"[ensure_directory_exists] - Checking directory: {directory}")
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.error(
            f"[ensure_directory_exists] - Failed to create directory {directory}: {str(e)}"
        )
        raise


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


def extract_info(url, extract_flat=False):
    """Extract video/playlist information using yt-dlp"""
    logger.info(f"[extract_info] - Extracting info from URL")

    ydl_opts = {"quiet": True}
    if extract_flat:
        ydl_opts["extract_flat"] = True

    logger.debug(f"[extract_info] - yt-dlp options: {ydl_opts}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"[extract_info] - Successfully extracted info")
            logger.debug(
                f"[extract_info] - Info keys: {list(info.keys()) if info else 'None'}"
            )
            return info
    except yt_dlp.utils.ExtractorError as e:
        error_msg = f"Cannot extract information from {url}: {str(e)}"
        logger.error(f"[extract_info] - ExtractorError: {error_msg}")
        raise VideoDownloadException(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error extracting info from {url}: {str(e)}"
        logger.error(f"[extract_info] - Unexpected error: {error_msg}")
        raise VideoDownloadException(error_msg)


def get_video_info(video_url: str) -> Union[Dict, List[Dict]]:
    """
    Get video or playlist information from YouTube URL

    Returns:
        Dict for single video or List[Dict] for playlist
    """
    logger.info(f"[get_video_info] - Processing URL")

    try:
        parsed_url = urlparse(video_url)
        query_params = parse_qs(parsed_url.query)
        playlist_id = query_params.get("list", [None])[0]

        logger.debug(f"[get_video_info] - Parsed URL: {parsed_url}")
        logger.debug(f"[get_video_info] - Query params: {query_params}")
        logger.debug(f"[get_video_info] - Playlist ID: {playlist_id}")

        if playlist_id:
            logger.info(f"[get_video_info] - Processing playlist: {playlist_id}")
            # Handle playlist
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            try:
                info = extract_info(playlist_url, extract_flat=True)
                if not info or not info.get("entries"):
                    error_msg = f"Playlist {playlist_id} is empty or does not exist"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)

                logger.info(
                    f"[get_video_info] - Found {len(info['entries'])} entries in playlist"
                )
                playlist_videos = []

                for i, entry in enumerate(info["entries"]):
                    logger.debug(
                        f"[get_video_info] - Processing entry {i+1}: {entry.get('title', 'Unknown')}"
                    )

                    if "url" in entry:
                        video_data = {
                            "id": entry.get("id", ""),
                            "title": entry.get("title", "Untitled"),
                            "url": entry["url"],
                            "duration": entry.get("duration", 0),
                            "thumbnail": (
                                entry.get("thumbnails", [{}])[0].get("url", "")
                                if entry.get("thumbnails")
                                else ""
                            ),
                            "uploader": entry.get("uploader", "Unknown"),
                            "view_count": entry.get("view_count", 0),
                        }
                        playlist_videos.append(video_data)
                        logger.debug(
                            f"[get_video_info] - Added video: {video_data['title']}"
                        )
                    else:
                        logger.warning(
                            f"[get_video_info] - Skipping entry without URL: {entry.get('title', 'Unknown')}"
                        )

                if not playlist_videos:
                    error_msg = f"No valid videos found in playlist {playlist_id}"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)

                result = {
                    "type": "playlist",
                    "title": info.get("title", "Untitled Playlist"),
                    "videos": playlist_videos,
                    "count": len(playlist_videos),
                }

                logger.info(
                    f"[get_video_info] - Successfully processed playlist: {result['title']} ({result['count']} videos)"
                )
                return result

            except Exception as e:
                if "does not exist" in str(e) or "private" in str(e):
                    error_msg = f"Playlist {playlist_id} does not exist or is private"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)
                else:
                    error_msg = f"Failed to access playlist {playlist_id}: {str(e)}"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)
        else:
            try:
                info = extract_info(video_url)
                video_info = {
                    "type": "video",
                    "id": info.get("id", ""),
                    "title": info.get("title", "Untitled"),
                    "duration": info.get("duration", 0),
                    "thumbnail": (
                        info.get("thumbnails", [{}])[0].get("url", "")
                        if info.get("thumbnails") and len(info.get("thumbnails")) > 0
                        else ""
                    ),
                    "url": video_url,
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                }

                logger.info(f"[get_video_info] - Successfully processed video")
                logger.info(
                    f"[get_video_info] - Video details: {json.dumps(video_info, indent=2)}"
                )
                logger.debug(f"[get_video_info] - Video info: {video_info}")
                return video_info

            except Exception as e:
                if "does not exist" in str(e) or "unavailable" in str(e):
                    error_msg = f"Video {video_url} does not exist or is unavailable"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)
                else:
                    error_msg = f"Failed to access video {video_url}: {str(e)}"
                    logger.error(f"[get_video_info] - {error_msg}")
                    raise VideoDownloadException(error_msg)

    except VideoDownloadException:
        raise  # Re-raise VideoDownloadException as-is
    except Exception as e:
        error_msg = f"Unexpected error processing URL {video_url}: {str(e)}"
        logger.error(f"[get_video_info] - {error_msg}")
        raise VideoDownloadException(error_msg)


class ProgressTracker:
    """Track download progress for multiple videos"""

    def __init__(self):
        self.progress = {}
        logger.info("[ProgressTracker.__init__] - Progress tracker initialized")

    def get_hook(self, video_id: str, callback=None):
        """Get progress hook for a specific video"""
        logger.debug(
            f"[ProgressTracker.get_hook] - Creating hook for video: {video_id}"
        )

        def progress_hook(d):
            status = d["status"]

            # Clean percent string and convert to float
            percent_str = re.sub(
                r"\x1b\[[0-9;]*m", "", d.get("_percent_str", "0%")
            ).strip()
            try:
                percent = float(percent_str.replace("%", ""))
            except ValueError:
                percent = 0.0

            # Initialize tracker for video if not exists
            if video_id not in self.progress:
                self.progress[video_id] = {
                    "last_percent": 0.0,
                    "reported_finished": False,
                }
                logger.debug(
                    f"[ProgressTracker.progress_hook] - Initialized tracking for: {video_id}"
                )

            # Update progress
            last_percent = self.progress[video_id]["last_percent"]

            if percent >= last_percent or status == "finished":
                self.progress[video_id]["last_percent"] = max(last_percent, percent)

                progress_data = {
                    "id": video_id,
                    "status": status,
                    "percent": (
                        100.0 if status == "finished" else float(f"{percent:.1f}")
                    ),
                    "total_bytes": d.get("total_bytes", "unknown"),
                }

                logger.debug(
                    f"[ProgressTracker.progress_hook] - Progress update for {video_id}: {progress_data['percent']:.1f}% ({status})"
                )

                if status == "finished" or percent >= 100.0:
                    if not self.progress[video_id]["reported_finished"]:
                        self.progress[video_id]["reported_finished"] = True
                        progress_data["percent"] = 100.0
                        logger.info(
                            f"[ProgressTracker.progress_hook] - Download completed for: {video_id}"
                        )

                # Call callback if provided
                if callback:
                    callback(progress_data)

        return progress_hook


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
    video_url: str,
    format_type: str = "video",
    audio_format: Optional[str] = "mp3",
    video_quality: Optional[str] = "720p",
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
        downloaded_files = []
        for file in os.listdir(output_dir):
            if file.startswith(video_title) and not file.endswith(".part"):
                downloaded_files.append(file)
                logger.debug(f"[download_single_video] - Found file: {file}")

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
        output_dir = os.path.join(os.getcwd(), "downloads")
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
                if progress_callback:
                    overall_progress = {
                        "id": "overall",
                        "status": "downloading",
                        "percent": float(
                            f"{(completed_count / total_videos) * 100:.1f}"
                        ),
                        "total_bytes": total_videos,
                        "current_video": completed_count,
                        "total_videos": total_videos,
                        "current_title": video_title,
                    }
                    progress_callback(overall_progress)
                    logger.debug(
                        f"[download_multiple_videos] - Overall progress: {overall_progress['percent']:.1f}% ({completed_count}/{total_videos})"
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
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
                    file_size = os.path.getsize(file_path)
                    logger.debug(
                        f"[download_multiple_videos] - Added to ZIP: {arcname} ({file_size} bytes)"
                    )
                else:
                    logger.warning(
                        f"[download_multiple_videos] - File not found, skipping: {file_path}"
                    )

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


def cleanup_temp_files(file_path: str):
    """Clean up temporary files and directories"""
    logger.info(f"[cleanup_temp_files] - Cleaning up: {file_path}")

    try:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                logger.info(
                    f"[cleanup_temp_files] - Removed file: {file_path} ({file_size} bytes)"
                )
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
                logger.info(f"[cleanup_temp_files] - Removed directory: {file_path}")
        else:
            logger.debug(f"[cleanup_temp_files] - Path does not exist: {file_path}")
    except Exception as e:
        logger.warning(
            f"[cleanup_temp_files] - Error cleaning up {file_path}: {str(e)}"
        )


def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS"""
    if seconds is None or seconds == 0:
        return "Unknown"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


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

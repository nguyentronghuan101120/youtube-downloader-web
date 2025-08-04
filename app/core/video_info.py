import json
import logging
import subprocess
import sys
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Union

from app.exceptions.custom_exceptions import VideoDownloadException

logger = logging.getLogger(__name__)

try:
    import yt_dlp
except ImportError:
    logger.warning("[IMPORT] - yt_dlp not found. Installing it now...")
    print("yt_dlp not found. Installing it now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
    logger.info("[IMPORT] - yt_dlp installed and imported successfully")


def extract_info(url: str, extract_flat: bool = False) -> Dict:
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


class VideoInfo:
    """Model class for video information"""
    
    def __init__(self, data: Dict):
        self.id = data.get("id", "")
        self.title = data.get("title", "Untitled")
        self.duration = data.get("duration", 0)
        self.thumbnail = data.get("thumbnail", "")
        self.url = data.get("url", "")
        self.uploader = data.get("uploader", "Unknown")
        self.view_count = data.get("view_count", 0)
        self.type = data.get("type", "video")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "url": self.url,
            "uploader": self.uploader,
            "view_count": self.view_count,
            "type": self.type,
        }


class PlaylistInfo:
    """Model class for playlist information"""
    
    def __init__(self, data: Dict):
        self.title = data.get("title", "Untitled Playlist")
        self.videos = [VideoInfo(video) for video in data.get("videos", [])]
        self.count = len(self.videos)
        self.type = "playlist"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "title": self.title,
            "videos": [video.to_dict() for video in self.videos],
            "count": self.count,
        } 
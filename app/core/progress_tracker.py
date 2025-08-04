import threading
import logging
from typing import Dict, Optional, Callable
from app.utils.formatters import clean_percent_string

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track download progress for multiple videos"""

    def __init__(self):
        self.progress = {}
        logger.info("[ProgressTracker.__init__] - Progress tracker initialized")

    def get_hook(self, video_id: str, callback: Optional[Callable] = None):
        """Get progress hook for a specific video"""
        logger.debug(
            f"[ProgressTracker.get_hook] - Creating hook for video: {video_id}"
        )

        def progress_hook(d):
            status = d["status"]

            # Clean percent string and convert to float
            percent_str = d.get("_percent_str", "0%")
            percent = clean_percent_string(percent_str)

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


# Global variables for progress tracking
progress_data = {}
progress_lock = threading.Lock()


def update_progress(progress_info: Dict) -> None:
    """Update global progress data"""
    with progress_lock:
        video_id = progress_info.get("id", "unknown")
        progress_data[video_id] = progress_info


def get_progress_status() -> Dict:
    """Get current progress status for all downloads"""
    with progress_lock:
        return progress_data.copy()


def clear_progress() -> None:
    """Clear all progress data"""
    with progress_lock:
        progress_data.clear()


def get_progress_for_video(video_id: str) -> Optional[Dict]:
    """Get progress for a specific video"""
    with progress_lock:
        return progress_data.get(video_id)


def update_overall_progress(
    completed_count: int,
    total_videos: int,
    current_title: str,
    callback: Optional[Callable] = None
) -> None:
    """Update overall progress for batch downloads"""
    overall_progress = {
        "id": "overall",
        "status": "downloading",
        "percent": float(f"{(completed_count / total_videos) * 100:.1f}"),
        "total_bytes": total_videos,
        "current_video": completed_count,
        "total_videos": total_videos,
        "current_title": current_title,
    }
    
    if callback:
        callback(overall_progress)
    
    logger.debug(
        f"[update_overall_progress] - Overall progress: {overall_progress['percent']:.1f}% ({completed_count}/{total_videos})"
    ) 
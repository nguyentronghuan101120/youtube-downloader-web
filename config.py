# Global configuration for YouTube Downloader
CONFIG = {
    "max_workers": 4,
    "supported_formats": ["video", "audio"],
    "supported_audio_formats": ["mp3", "m4a", "wav", "flac", "aac"],
    "default_audio_format": "mp3",
    "default_video_quality": "1080p",
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
    "log_level": "INFO",
    "temp_dir": "temp",
    "downloads_dir": "downloads"
} 
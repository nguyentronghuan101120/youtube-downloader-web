import re
from typing import Union


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


def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human readable format"""
    if bytes_size is None or bytes_size == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    
    return f"{bytes_size:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    # Remove invalid characters for filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def format_view_count(view_count: int) -> str:
    """Format view count to human readable format"""
    if view_count is None or view_count == 0:
        return "0 views"
    
    if view_count >= 1000000:
        return f"{view_count/1000000:.1f}M views"
    elif view_count >= 1000:
        return f"{view_count/1000:.1f}K views"
    else:
        return f"{view_count} views"


def clean_percent_string(percent_str: str) -> float:
    """Clean percent string and convert to float"""
    # Remove ANSI color codes and convert to float
    cleaned = re.sub(r"\x1b\[[0-9;]*m", "", percent_str).strip()
    try:
        return float(cleaned.replace("%", ""))
    except ValueError:
        return 0.0 
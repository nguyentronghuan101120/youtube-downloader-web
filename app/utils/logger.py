import logging
import sys
from config import CONFIG


def setup_logger():
    """Setup detailed logging configuration"""
    logging.basicConfig(
        level=getattr(logging, CONFIG["log_level"]),
        format="[%(levelname)s] - %(message)s\n",
        handlers=[
            logging.FileHandler("youtube_downloader.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_logger(name):
    """Get logger instance for a specific module"""
    return logging.getLogger(name)


class LogFormatter:
    """Custom formatter for log messages"""
    
    def __init__(self):
        self.formatter = logging.Formatter("[%(levelname)s] - %(message)s\n")
    
    def format(self, record):
        return self.formatter.format(record) 
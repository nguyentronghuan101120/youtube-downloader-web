import os
import shutil
import zipfile
import tempfile
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory: str) -> None:
    """Create directory if it doesn't exist"""
    logger.debug(f"[ensure_directory_exists] - Checking directory: {directory}")
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.error(
            f"[ensure_directory_exists] - Failed to create directory {directory}: {str(e)}"
        )
        raise


def cleanup_temp_files(file_path: str) -> None:
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


def create_zip_file(file_paths: List[str], output_path: str) -> None:
    """Create a ZIP file from a list of file paths"""
    logger.info(f"[create_zip_file] - Creating ZIP: {output_path}")
    
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
                    file_size = os.path.getsize(file_path)
                    logger.debug(
                        f"[create_zip_file] - Added to ZIP: {arcname} ({file_size} bytes)"
                    )
                else:
                    logger.warning(
                        f"[create_zip_file] - File not found, skipping: {file_path}"
                    )
        
        zip_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        logger.info(f"[create_zip_file] - ZIP created successfully: {output_path} ({zip_size} bytes)")
        
    except Exception as e:
        logger.error(f"[create_zip_file] - Error creating ZIP: {str(e)}")
        raise


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    except Exception as e:
        logger.warning(f"[get_file_size] - Error getting file size for {file_path}: {str(e)}")
        return 0


def find_downloaded_files(directory: str, prefix: str) -> List[str]:
    """Find downloaded files in directory with given prefix"""
    downloaded_files = []
    try:
        for file in os.listdir(directory):
            if file.startswith(prefix) and not file.endswith(".part"):
                downloaded_files.append(file)
                logger.debug(f"[find_downloaded_files] - Found file: {file}")
    except Exception as e:
        logger.error(f"[find_downloaded_files] - Error searching directory {directory}: {str(e)}")
    
    return downloaded_files


def create_temp_directory() -> str:
    """Create a temporary directory for downloads"""
    temp_dir = tempfile.mkdtemp()
    logger.debug(f"[create_temp_directory] - Created temp directory: {temp_dir}")
    return temp_dir


def get_downloads_directory() -> str:
    """Get the downloads directory path"""
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    ensure_directory_exists(downloads_dir)
    return downloads_dir 
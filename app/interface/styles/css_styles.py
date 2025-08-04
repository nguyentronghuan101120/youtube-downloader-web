# Custom CSS styles for the YouTube Downloader interface

PLAYLIST_CSS = """
<style>
.playlist-checkbox-group .gr-checkbox-group {
    max-height: 450px;
    overflow-y: auto;
    border: 2px solid #74b9ff;
    border-radius: 12px;
    padding: 16px;
    background: linear-gradient(135deg, #ffffff 0%, #f8fcff 100%);
    box-shadow: 0 4px 16px rgba(116, 185, 255, 0.1);
}
.playlist-checkbox-group .gr-checkbox {
    margin: 10px 0;
    padding: 12px;
    border: 1px solid #e3f2fd;
    border-radius: 8px;
    background: white;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.playlist-checkbox-group .gr-checkbox:hover {
    background: #e3f2fd;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(116, 185, 255, 0.2);
}
.playlist-checkbox-group .gr-checkbox input:checked + label {
    color: #0984e3;
    font-weight: 600;
}
.playlist-checkbox-group label {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #2d3436;
}
/* Scrollbar styling */
.playlist-checkbox-group .gr-checkbox-group::-webkit-scrollbar {
    width: 8px;
}
.playlist-checkbox-group .gr-checkbox-group::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}
.playlist-checkbox-group .gr-checkbox-group::-webkit-scrollbar-thumb {
    background: #74b9ff;
    border-radius: 4px;
}
.playlist-checkbox-group .gr-checkbox-group::-webkit-scrollbar-thumb:hover {
    background: #0984e3;
}
</style>
"""

PREVIEW_CSS = """
<style>
.preview-container {
    border-radius: 10px;
    padding: 20px;
    margin: 16px 0;
}
.preview-video {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    color: white;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}
.preview-playlist {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    color: white;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}
.preview-error {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
    color: white;
    box-shadow: 0 4px 16px rgba(231, 76, 60, 0.3);
}
.preview-warning {
    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
    color: white;
    box-shadow: 0 4px 16px rgba(243, 156, 18, 0.3);
}
</style>
"""

PROGRESS_CSS = """
<style>
.progress-container {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
    color: white;
    box-shadow: 0 4px 16px rgba(116, 185, 255, 0.3);
}
.progress-bar {
    width: 100%;
    height: 20px;
    background-color: rgba(255,255,255,0.2);
    border-radius: 10px;
    overflow: hidden;
    margin: 10px 0;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00b894 0%, #00cec9 100%);
    transition: width 0.3s ease;
    border-radius: 10px;
}
</style>
"""

MAIN_CSS = """
<style>
.main-container {
    max-width: 800px;
    margin: 0 auto;
}
.preview-box {
    border-radius: 10px;
    padding: 20px;
}
.download-placeholder {
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
}
</style>
"""


def get_custom_css() -> str:
    """Get all custom CSS styles combined"""
    return MAIN_CSS + PREVIEW_CSS + PLAYLIST_CSS + PROGRESS_CSS


def get_playlist_css() -> str:
    """Get playlist-specific CSS"""
    return PLAYLIST_CSS


def get_preview_css() -> str:
    """Get preview-specific CSS"""
    return PREVIEW_CSS


def get_progress_css() -> str:
    """Get progress-specific CSS"""
    return PROGRESS_CSS 
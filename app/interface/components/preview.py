import logging
from typing import Tuple, List
from config import CONFIG
from app.core.video_info import get_video_info
from app.core.validators import validate_youtube_url
from app.utils.formatters import format_duration, format_view_count
from app.exceptions.custom_exceptions import VideoDownloadException
from app.interface.styles.css_styles import get_preview_css

logger = logging.getLogger(__name__)


def get_loading_preview_html() -> str:
    """
    Generates a placeholder HTML for the preview section.
    """
    return """
    <div style="
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
    ">
        <p style="font-size: 1.1em; font-weight: 600; margin: 0;">Video preview will be appear here</p>
    </div>
    """


def preview_video(url: str) -> Tuple[str, str, str, List, str]:
    """
    Preview video or playlist information with enhanced UI

    Returns:
        (preview_html, format_choice_visibility, playlist_visibility, playlist_choices, error_message)
    """
    if not url.strip():
        return get_loading_preview_html(), "hidden", "hidden", [], ""

    if not validate_youtube_url(url):
        return (
            "",
            "hidden",
            "hidden",
            [],
            "❌ Invalid YouTube URL. Please enter a valid YouTube video or playlist URL.",
        )

    try:
        info = get_video_info(url)

        if info.get("type") == "playlist":
            # Enhanced Playlist preview
            videos = info.get("videos", [])
            playlist_title = info.get("title", "Unknown Playlist")
            total_duration = sum(v.get("duration", 0) for v in videos)

            preview_html = f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
                padding: 24px;
                margin: 16px 0;
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="
                        background: rgba(255,255,255,0.2);
                        border-radius: 12px;
                        padding: 12px;
                        margin-right: 16px;
                        backdrop-filter: blur(10px);
                    ">
                        <span style="font-size: 24px;">📋</span>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.4em; font-weight: 600;">
                            Playlist Preview
                        </h3>
                        <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 0.9em;">
                            {playlist_title}
                        </p>
                    </div>
                </div>
                
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin-top: 20px;
                ">
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="font-size: 2em; margin-bottom: 8px;">🎬</div>
                        <div style="font-size: 1.2em; font-weight: 600;">{len(videos)}</div>
                        <div style="font-size: 0.85em; opacity: 0.8;">Videos</div>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="font-size: 2em; margin-bottom: 8px;">⏱️</div>
                        <div style="font-size: 1.2em; font-weight: 600;">{format_duration(total_duration)}</div>
                        <div style="font-size: 0.85em; opacity: 0.8;">Total Duration</div>
                    </div>
                </div>
            </div>
            """

            # Enhanced playlist choices
            playlist_choices = []
            for i, video in enumerate(videos):
                duration_str = format_duration(video.get("duration", 0))
                title = video.get("title", "Untitled")

                # Create clear, informative text label
                choice_label = f"{i+1:02d}. {title[:60] + ('...' if len(title) > 60 else '')} | ⏱️ {duration_str}"
                playlist_choices.append((choice_label, i))

            # Add custom CSS for better playlist display
            playlist_css = get_preview_css()

            return (
                preview_html + playlist_css,
                "visible",
                "visible",
                playlist_choices,
                "",
            )

        else:
            # Enhanced Single video preview
            title = info.get("title", "Unknown Title")
            duration = format_duration(info.get("duration", 0))
            thumbnail = info.get("thumbnail", "")
            uploader = info.get("uploader", "Unknown Channel")
            view_count = info.get("view_count", 0)

            # Format view count
            view_str = format_view_count(view_count)

            thumbnail_section = ""
            if thumbnail:
                thumbnail_section = f"""
                <div style="
                    position: relative;
                    margin-bottom: 20px;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                ">
                    <img src="{thumbnail}" style="
                        width: 100%;
                        height: auto;
                        max-height: 320px;
                        object-fit: cover;
                        display: block;
                    ">
                    <div style="
                        position: absolute;
                        bottom: 8px;
                        right: 8px;
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 0.85em;
                        font-weight: 600;
                    ">
                        {duration}
                    </div>
                </div>
                """

            preview_html = f"""
            <div style="
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                border-radius: 16px;
                padding: 24px;
                margin: 16px 0;
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="
                        background: rgba(255,255,255,0.2);
                        border-radius: 12px;
                        padding: 12px;
                        margin-right: 16px;
                        backdrop-filter: blur(10px);
                    ">
                        <span style="font-size: 24px;">🎬</span>
                    </div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0; font-size: 1.4em; font-weight: 600;">
                            Video Preview
                        </h3>
                        <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 0.9em;">
                            Ready to download
                        </p>
                    </div>
                </div>

                {thumbnail_section}

                <div style="margin-bottom: 16px;">
                    <h4 style="
                        margin: 0 0 12px 0;
                        font-size: 1.2em;
                        font-weight: 600;
                        line-height: 1.4;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        {title}
                    </h4>
                </div>

                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 12px;
                    margin-top: 16px;
                ">
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="font-size: 1.1em; font-weight: 600; margin-bottom: 4px;">
                            {duration}
                        </div>
                        <div style="font-size: 0.8em; opacity: 0.8;">Duration</div>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="font-size: 1.1em; font-weight: 600; margin-bottom: 4px;">
                            {view_str}
                        </div>
                        <div style="font-size: 0.8em; opacity: 0.8;">Views</div>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                        grid-column: span 2;
                    ">
                        <div style="font-size: 1.1em; font-weight: 600; margin-bottom: 4px;">
                            {uploader}
                        </div>
                        <div style="font-size: 0.8em; opacity: 0.8;">Channel</div>
                    </div>
                </div>
            </div>
            """

            return preview_html, "visible", "hidden", [], ""

    except VideoDownloadException as e:
        # Enhanced error display
        error_html = f"""
        <div style="
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            color: white;
            box-shadow: 0 4px 16px rgba(231, 76, 60, 0.3);
        ">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 24px; margin-right: 12px;">❌</span>
                <div>
                    <h4 style="margin: 0; font-weight: 600;">Download Error</h4>
                    <p style="margin: 4px 0 0 0; opacity: 0.9;">{str(e)}</p>
                </div>
            </div>
        </div>
        """
        return error_html, "hidden", "hidden", [], ""

    except Exception as e:
        # Enhanced unexpected error display
        error_html = f"""
        <div style="
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            color: white;
            box-shadow: 0 4px 16px rgba(243, 156, 18, 0.3);
        ">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 24px; margin-right: 12px;">⚠️</span>
                <div>
                    <h4 style="margin: 0; font-weight: 600;">Unexpected Error</h4>
                    <p style="margin: 4px 0 0 0; opacity: 0.9;">{str(e)}</p>
                </div>
            </div>
        </div>
        """
        return error_html, "hidden", "hidden", [], ""


def create_video_preview(video_info: dict) -> str:
    """Create preview HTML for a single video"""
    title = video_info.get("title", "Unknown Title")
    duration = format_duration(video_info.get("duration", 0))
    thumbnail = video_info.get("thumbnail", "")
    uploader = video_info.get("uploader", "Unknown Channel")
    view_count = video_info.get("view_count", 0)
    view_str = format_view_count(view_count)

    return f"""
    <div class="preview-video">
        <h3>{title}</h3>
        <p>Duration: {duration}</p>
        <p>Channel: {uploader}</p>
        <p>Views: {view_str}</p>
    </div>
    """


def create_playlist_preview(playlist_info: dict) -> str:
    """Create preview HTML for a playlist"""
    title = playlist_info.get("title", "Unknown Playlist")
    videos = playlist_info.get("videos", [])
    total_duration = sum(v.get("duration", 0) for v in videos)

    return f"""
    <div class="preview-playlist">
        <h3>{title}</h3>
        <p>Videos: {len(videos)}</p>
        <p>Total Duration: {format_duration(total_duration)}</p>
    </div>
    """ 
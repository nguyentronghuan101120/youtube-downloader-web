import gradio as gr
import os
import tempfile
import threading
import time
import multiprocessing
from typing import Optional, Dict, List, Tuple, Any

from youtube_downloader import (
    get_video_info,
    download_single_video,
    download_multiple_videos,
    cleanup_temp_files,
    format_duration,
    validate_youtube_url,
    ensure_directory_exists,
    VideoDownloadException,
    CONFIG,
)

# Global variables for progress tracking
progress_data = {}
progress_lock = threading.Lock()


def update_progress(progress_info: Dict):
    """Update global progress data"""
    with progress_lock:
        video_id = progress_info.get("id", "unknown")
        progress_data[video_id] = progress_info


def get_progress_status():
    """Get current progress status for all downloads"""
    with progress_lock:
        return progress_data.copy()


# --- UI Components ---
def get_loading_preview_html() -> str:
    """
    Generates a placeholder HTML for the preview section.
    """
    return """
    <div style="
        /* background: #f0f0f0; Light grey background */
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 150px; /* Set a fixed height to prevent layout shifts */
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
            playlist_css = """
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
            if view_count >= 1000000:
                view_str = f"{view_count/1000000:.1f}M views"
            elif view_count >= 1000:
                view_str = f"{view_count/1000:.1f}K views"
            else:
                view_str = f"{view_count} views"

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


def download_content(
    url: str,
    format_type: str,
    audio_format: Optional[str],
    video_quality: Optional[str],
    selected_videos: List[int] = None,
) -> Tuple[Optional[str], str]:
    """
    Download video(s) based on user selection

    Returns:
        (file_path, status_message)
    """
    if not url.strip():
        return None, "❌ Please enter a YouTube URL"

    if not validate_youtube_url(url):
        return None, "❌ Invalid YouTube URL"

    try:
        # Clear previous progress
        with progress_lock:
            progress_data.clear()

        # Validate and set default values based on format type
        if format_type == "video":
            video_quality = video_quality or "1080p"
            audio_format = None  # Not used for video downloads
        elif format_type == "audio":
            audio_format = audio_format or CONFIG["default_audio_format"]
            video_quality = None  # Not used for audio downloads
        else:
            return None, f"❌ Invalid format type: {format_type}"

        # Create downloads directory in current working directory
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        ensure_directory_exists(downloads_dir)

        info = get_video_info(url)

        if info.get("type") == "playlist":
            videos = info.get("videos", [])

            # Filter selected videos if specified
            if selected_videos:
                videos = [videos[i] for i in selected_videos if i < len(videos)]

            if not videos:
                return None, "❌ No videos selected or found"

            if len(videos) == 1:
                # Single video from playlist
                file_path = download_single_video(
                    videos[0],
                    format_type,
                    audio_format,
                    video_quality,
                    output_dir=downloads_dir,
                    progress_callback=update_progress,
                )
            else:
                # Multiple videos - create ZIP with parallel downloads using all CPU cores
                file_path = download_multiple_videos(
                    videos,
                    format_type,
                    audio_format,
                    video_quality,
                    progress_callback=update_progress,
                    max_workers=None,  # Auto-detect and use all CPU cores
                    output_dir=downloads_dir,  # Save ZIP to downloads directory
                )

            count = len(videos)
            if count > 1:
                cpu_cores = multiprocessing.cpu_count()
                success_msg = f"✅ Successfully downloaded {count} videos using parallel processing ({cpu_cores} CPU cores utilized)"
            else:
                success_msg = f"✅ Successfully downloaded {count} video"
            return (
                file_path,
                success_msg,
            )

        else:
            # Single video
            file_path = download_single_video(
                info,
                format_type,
                audio_format,
                video_quality,
                output_dir=downloads_dir,
                progress_callback=update_progress,
            )
            return file_path, "✅ Successfully downloaded video"

    except VideoDownloadException as e:
        return None, f"❌ Download error: {str(e)}"
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"


def get_download_placeholder_html() -> str:
    """
    Generates a placeholder HTML for the download content section.
    """
    return """
    <div style="
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        text-align: center;
        height: 80px; /* Adjust height as needed */
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px dashed #ccc;
        color: #888;
    ">
        <p style="font-size: 1em; font-weight: 500; margin: 0;">Download status will appear here after a successful download.</p>
    </div>
    """


def create_interface():
    """Create and configure the Gradio interface"""

    with gr.Blocks(
        title="🎬 YouTube Downloader",
        theme=gr.themes.Soft(),
        css="""
        .main-container {
            max-width: 800px;
            margin: 0 auto;
        }
        .preview-box {
            border-radius: 10px;
            padding: 20px;
        }
        """,
    ) as interface:

        gr.HTML(
            """
        <div style="text-align: center; padding: 20px;">
            <h1>🎬 YouTube Downloader</h1>
            <p>Download YouTube videos and playlists in various formats</p>
        </div>
        """
        )

        # Input and Analyze Section
        url_input = gr.Textbox(
            label="📎 YouTube URL",
            placeholder="Paste YouTube video or playlist URL here, then click Analyze button...",
            lines=1,
        )

        # Analyze section
        with gr.Row():
            analyze_btn = gr.Button(
                "🔍 Analyze Video/Playlist", variant="secondary", size="lg"
            )

        # Preview section
        preview_output = gr.HTML(
            value=get_loading_preview_html(), label="Preview", visible=True
        )
        error_output = gr.HTML(visible=False)

        # Format selection using tabs only (initially hidden)
        with gr.Group(visible=False) as format_group:
            # Hidden state to track current format type
            format_type_state = gr.State(value="video")

            with gr.Tabs(selected=0) as format_tabs:
                with gr.TabItem("🎥 Video Options") as video_tab:
                    video_quality = gr.Dropdown(
                        choices=CONFIG["video_qualities"],
                        value="1080p",  # Set to 1080p as requested
                        label="🎥 Video Quality",
                    )
                with gr.TabItem("🎵 Audio Options") as audio_tab:
                    audio_format = gr.Dropdown(
                        choices=CONFIG["supported_audio_formats"],
                        value=CONFIG["default_audio_format"],
                        label="🎵 Audio Format",
                    )

        # Playlist selection (initially hidden)
        with gr.Group(visible=False) as playlist_group:
            cpu_cores = multiprocessing.cpu_count()
            playlist_header_html = f"""
            <div style="
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 16px 0;
                color: white;
                box-shadow: 0 4px 16px rgba(116, 185, 255, 0.3);
            ">
                <h4 style="margin: 0 0 12px 0; color: white; font-size: 18px; font-weight: 600;">
                    📋 Select Videos to Download
                </h4>
                <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 14px;">
                    🚀 Ultra-fast parallel downloading using all {cpu_cores} CPU cores simultaneously!<br/>
                    Format: <strong>Number. Title | ⏱️ Duration</strong>
                </p>
            </div>
            """
            gr.HTML(playlist_header_html)
            playlist_videos = gr.CheckboxGroup(
                choices=[],
                label="",  # Remove default label since we have custom header
                value=[],
                elem_classes=["playlist-checkbox-group"],
            )
            with gr.Row():
                select_all_btn = gr.Button(
                    "✅ Select All", size="sm", variant="secondary"
                )
                deselect_all_btn = gr.Button(
                    "❌ Deselect All", size="sm", variant="secondary"
                )

        # Download section (initially hidden)
        with gr.Group(visible=False) as download_group:
            with gr.Row():
                download_btn = gr.Button(
                    "⬇️ Download Selected", variant="primary", size="lg"
                )

        # Output section
        with gr.Group() as output_group:
            status_output = gr.HTML(value=get_download_placeholder_html())
            file_output = gr.File(label="📥 Downloaded File", visible=False)

        # Progress section (initially hidden)
        with gr.Group(visible=False) as progress_group:
            progress_html = gr.HTML()

        # Event handlers
        def on_analyze(url):
            nonlocal current_playlist_choices
            preview_html, format_vis, playlist_vis, playlist_choices, error_msg = (
                preview_video(url)
            )

            # Update global playlist choices for select all functionality
            current_playlist_choices = playlist_choices

            # Show download section if analysis successful
            download_vis = format_vis == "visible"

            updates = [
                gr.update(
                    value=preview_html, visible=bool(preview_html)
                ),  # preview_output
                gr.update(value=error_msg, visible=bool(error_msg)),  # error_output
                gr.update(visible=format_vis == "visible"),  # format_group
                gr.update(visible=playlist_vis == "visible"),  # playlist_group
                gr.update(choices=playlist_choices, value=[]),  # playlist_videos
                gr.update(visible=download_vis),  # download_group
            ]
            return updates

        # Store playlist choices globally for select all functionality
        current_playlist_choices = []

        def on_download(url, format_type, audio_format, video_quality, selected_videos):
            print(f"DEBUG: on_download called with format_type={format_type}")

            # For video tab, ensure we use 1080p quality and ignore audio_format
            if format_type == "video":
                video_quality = "1080p"
                audio_format = None  # Not used for video downloads
                print(
                    f"DEBUG: Video mode - quality={video_quality}, audio_format={audio_format}"
                )

            # For audio tab, ignore video quality
            if format_type == "audio":
                video_quality = None  # Not used for audio downloads
                print(
                    f"DEBUG: Audio mode - audio_format={audio_format}, video_quality={video_quality}"
                )

            file_path, status_msg = download_content(
                url, format_type, audio_format, video_quality, selected_videos
            )

            if file_path:
                return (
                    gr.update(value=status_msg),  # status_output
                    gr.update(value=file_path, visible=True),  # file_output
                    gr.update(visible=True),  # progress_group
                )
            else:
                return (
                    gr.update(value=status_msg),  # status_output
                    gr.update(visible=False),  # file_output
                    gr.update(visible=False),  # progress_group
                )

        # Connect event handlers - ĐÃ XÓA url_input.change()
        analyze_btn.click(
            on_analyze,
            inputs=[url_input],
            outputs=[
                preview_output,
                error_output,
                format_group,
                playlist_group,
                playlist_videos,
                download_group,
            ],
        )

        def on_select_all():
            # Select all available video indices using the actual values from choices
            if current_playlist_choices:
                return [
                    choice[1] for choice in current_playlist_choices
                ]  # Return the values, not indices
            return []

        def on_deselect_all():
            return []

        select_all_btn.click(on_select_all, outputs=[playlist_videos])

        deselect_all_btn.click(on_deselect_all, outputs=[playlist_videos])

        # Tab change handlers to update format state
        video_tab.select(lambda: "video", outputs=[format_type_state])
        audio_tab.select(lambda: "audio", outputs=[format_type_state])

        download_btn.click(
            on_download,
            inputs=[
                url_input,
                format_type_state,  # Use state instead of tabs
                audio_format,
                video_quality,
                playlist_videos,
            ],
            outputs=[status_output, file_output, progress_group],
        )

    return interface


if __name__ == "__main__":
    # Create the interface
    app = create_interface()

    # Launch the app
    app.launch(
        server_name="0.0.0.0",  # Allow external access (needed for HF Spaces)
        server_port=7860,  # Standard port for HF Spaces
        show_error=True,
        share=False,
        debug=True,  # Enable hot reloading for development
    )

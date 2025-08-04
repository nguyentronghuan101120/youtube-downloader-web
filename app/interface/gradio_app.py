import gradio as gr
import multiprocessing
import logging
from typing import List

from config import CONFIG
from app.interface.components.preview import preview_video, get_loading_preview_html
from app.interface.components.download import download_content, get_download_placeholder_html
from app.interface.styles.css_styles import get_custom_css

logger = logging.getLogger(__name__)


def create_interface():
    """Create and configure the Gradio interface"""

    with gr.Blocks(
        title="🎬 YouTube Downloader",
        theme=gr.themes.Soft(),
        css=get_custom_css(),
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

        # Connect event handlers
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


def setup_event_handlers(interface):
    """Setup additional event handlers if needed"""
    # This function can be used to add more event handlers
    # or modify existing ones
    pass 
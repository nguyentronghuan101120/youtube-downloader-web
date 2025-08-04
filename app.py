#!/usr/bin/env python3
"""
YouTube Downloader - Main Entry Point

A modular YouTube downloader application with a Gradio web interface.
"""

from app.utils.logger import setup_logger
from app.interface.gradio_app import create_interface


def main():
    """Main entry point for the YouTube Downloader application"""
    # Setup logging
    setup_logger()

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


if __name__ == "__main__":
    main()

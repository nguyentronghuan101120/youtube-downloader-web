# 🎬 YouTube Downloader Web App

A modular and user-friendly web application for downloading YouTube videos and playlists using Gradio interface.

## ✨ Features

- **Single Video Download**: Download individual YouTube videos
- **Playlist Support**: Download entire playlists or select specific videos
- **Multiple Formats**: Support for video (MP4/MKV) and audio-only downloads
- **Quality Selection**: Choose from 240p to 4K or best available quality
- **Audio Formats**: MP3, M4A, WAV, FLAC, AAC support
- **Real-time Preview**: Preview video/playlist information before downloading
- **Progress Tracking**: Real-time download progress updates
- **Batch Downloads**: Multiple videos packaged in ZIP files
- **Clean Interface**: Intuitive Gradio-based web interface
- **Modular Architecture**: Well-organized, maintainable codebase

## 🚀 Quick Start

### Local Development

1. **Clone the repository**

```bash
git clone <repository-url>
cd youtube-downloader
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the application**

```bash
python app.py
```

4. **Open your browser**
   Navigate to `http://localhost:7860`

### Hugging Face Spaces Deployment

This app is designed to be deployed on Hugging Face Spaces:

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Upload all files to your Space repository
3. The app will automatically deploy and be available at your Space URL

## 📖 How to Use

### Single Video Download

1. **Enter URL**: Paste a YouTube video URL in the input field
2. **Preview**: Click "Preview" to see video information
3. **Select Format**: Choose between video or audio-only download
4. **Choose Quality**: Select video quality (for video downloads) or audio format
5. **Download**: Click "Download" to start the process

### Playlist Download

1. **Enter Playlist URL**: Paste a YouTube playlist URL
2. **Preview**: The app will show all videos in the playlist
3. **Select Videos**: Use checkboxes to select which videos to download
4. **Select Format & Quality**: Choose your preferred format and quality
5. **Download**: The app will create a ZIP file with all selected videos

## 🎛️ Supported Formats

### Video Formats

- **Qualities**: 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p (4K), Best
- **Container**: MKV (with embedded thumbnails)

### Audio Formats

- **MP3**: Most compatible, good compression
- **M4A**: High quality, smaller file size
- **WAV**: Uncompressed, largest file size
- **FLAC**: Lossless compression
- **AAC**: Good quality, small file size

## 🔧 Technical Details

### Dependencies

- **Gradio**: Web interface framework
- **yt-dlp**: YouTube download engine
- **FFmpeg**: Audio/video processing (auto-detected or bundled)

### Project Structure

```
youtube-downloader/
├── app.py                    # Main entry point
├── config.py                 # Global configuration
├── app/                      # Main application package
│   ├── __init__.py
│   ├── core/                 # Business logic
│   │   ├── __init__.py
│   │   ├── downloader.py     # Download functionality
│   │   ├── video_info.py     # Video/playlist info extraction
│   │   ├── progress_tracker.py # Progress tracking
│   │   └── validators.py     # Input validation
│   ├── interface/            # User interface
│   │   ├── __init__.py
│   │   ├── gradio_app.py     # Main Gradio interface
│   │   ├── components/       # UI components
│   │   │   ├── __init__.py
│   │   │   ├── preview.py    # Video preview functionality
│   │   │   └── download.py   # Download handling
│   │   └── styles/           # CSS styles
│   │       ├── __init__.py
│   │       └── css_styles.py # Custom CSS
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   ├── file_manager.py   # File operations
│   │   ├── ffmpeg_checker.py # FFmpeg detection
│   │   ├── formatters.py     # Data formatting
│   │   └── logger.py         # Logging setup
│   └── exceptions/           # Custom exceptions
│       ├── __init__.py
│       └── custom_exceptions.py
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── downloads/               # Downloaded files directory
└── logs/                   # Log files directory
```

### Key Features

- **Modular Design**: Clean separation of concerns with dedicated modules
- **Progress Tracking**: Real-time download progress with percentage updates
- **Error Handling**: Comprehensive error messages and graceful failure handling
- **Temporary Files**: Automatic cleanup of temporary files
- **FFmpeg Detection**: Automatic detection of FFmpeg from multiple sources
- **URL Validation**: Validates YouTube URLs before processing
- **Scalable Architecture**: Easy to extend and maintain

## 🏗️ Architecture Overview

### Core Modules (`app/core/`)

- **downloader.py**: Handles all download operations using yt-dlp
- **video_info.py**: Extracts and processes video/playlist information
- **progress_tracker.py**: Manages download progress tracking
- **validators.py**: Validates user inputs and parameters

### Interface Modules (`app/interface/`)

- **gradio_app.py**: Main Gradio interface creation and event handling
- **components/preview.py**: Video and playlist preview functionality
- **components/download.py**: Download request handling
- **styles/css_styles.py**: Custom CSS styling

### Utility Modules (`app/utils/`)

- **file_manager.py**: File and directory operations
- **ffmpeg_checker.py**: FFmpeg availability detection
- **formatters.py**: Data formatting utilities
- **logger.py**: Logging configuration

### Exception Handling (`app/exceptions/`)

- **custom_exceptions.py**: Custom exception classes for better error handling

## ⚠️ Important Notes

### Legal Considerations

- **Respect Copyright**: Only download content you have permission to download
- **YouTube Terms**: Ensure compliance with YouTube's Terms of Service
- **Personal Use**: This tool is intended for personal, non-commercial use
- **Fair Use**: Respect content creators' rights and fair use policies

### Technical Limitations

- **FFmpeg Required**: Audio processing requires FFmpeg (usually bundled)
- **Storage Space**: Large videos require adequate storage space
- **Network Speed**: Download speed depends on your internet connection
- **Rate Limiting**: YouTube may limit download speeds or block excessive requests

### Troubleshooting

#### Common Issues

1. **"FFmpeg not found"**: Ensure FFmpeg is installed or available in PATH
2. **"Video unavailable"**: Video may be private, deleted, or region-restricted
3. **"Download failed"**: Check internet connection and try again
4. **"Invalid URL"**: Ensure you're using a valid YouTube URL

#### Error Messages

- **URL Validation Errors**: Check that your URL is a valid YouTube link
- **Download Errors**: Usually network-related or video availability issues
- **Format Errors**: Some videos may not support all quality options

## 🛠️ Development

### Adding Features

The modular design makes it easy to add new features:

- **New download formats**: Add to `config.py` and update `app/core/downloader.py`
- **UI improvements**: Modify `app/interface/components/` modules
- **Core functionality**: Extend `app/core/` modules
- **Utilities**: Add to `app/utils/` modules

### Testing

```bash
# Run the application
python app.py

# Check logs
tail -f youtube_downloader.log
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep modules focused on single responsibilities

## 📝 License

This project is for educational and personal use. Please respect YouTube's Terms of Service and copyright laws.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

### Development Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes**: Follow the modular structure
4. **Test thoroughly**: Ensure all functionality works
5. **Submit a pull request**: Include clear description of changes

---

**Disclaimer**: This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with applicable laws and terms of service.

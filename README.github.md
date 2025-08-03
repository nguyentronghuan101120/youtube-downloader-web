# 🎬 YouTube Downloader Web App

A simple and user-friendly web application for downloading YouTube videos and playlists using Gradio interface.

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

### File Structure

```
youtube-downloader/
├── app.py                 # Main Gradio application
├── youtube_downloader.py  # Core download functionality
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── main.py              # Original CLI version (for reference)
```

### Key Features

- **Progress Tracking**: Real-time download progress with percentage updates
- **Error Handling**: Comprehensive error messages and graceful failure handling
- **Temporary Files**: Automatic cleanup of temporary files
- **FFmpeg Detection**: Automatic detection of FFmpeg from multiple sources
- **URL Validation**: Validates YouTube URLs before processing

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

### Project Structure

The app is built with a modular design:

- `app.py`: Gradio interface and user interaction logic
- `youtube_downloader.py`: Core download functionality and utilities
- Clean separation between UI and business logic

### Adding Features

The modular design makes it easy to add new features:

- New download formats can be added to the CONFIG
- UI improvements can be made in `app.py`
- Core functionality extensions go in `youtube_downloader.py`

## 📝 License

This project is for educational and personal use. Please respect YouTube's Terms of Service and copyright laws.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

---

**Disclaimer**: This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with applicable laws and terms of service.

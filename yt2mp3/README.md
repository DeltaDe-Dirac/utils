# utils

A collection of utility scripts for common tasks.

---

## 🎵 `yt2mp3` - YouTube to MP3 Converter

Convert YouTube videos to high-quality MP3 files with intelligent caching, metadata embedding, and optional time trimming.

### ✨ Features

- **Full video or trimmed clips** - Export entire videos or specific sections
- **Smart caching** - Download once, trim multiple times from cached source
- **Metadata embedding** - Includes title and artist information in MP3
- **Progress indicators** - Real-time download and conversion progress
- **Playlist detection** - Warns and rejects playlist URLs (single videos only)
- **Custom output directory** - Save files wherever you want
- **Quality options** - Configurable audio bitrate (default: 320K)
- **Verbose logging** - Debug mode for troubleshooting
- **Cross-platform** - Works on Windows, macOS, and Linux

### 🚀 Quick Start

#### 1. Run Setup Script

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```powershell
.\setup.bat
```

The setup script will:
- Check for Python 3
- Install `yt-dlp` if missing
- Install `ffmpeg` if missing
- Create cache directory

#### 2. Convert a Video

**Full video:**
```bash
python yt2mp3/yt_to_mp3.py "https://youtube.com/watch?v=VIDEO_ID"
```

**Trimmed clip:**
```bash
python yt2mp3/yt_to_mp3.py "https://youtube.com/watch?v=VIDEO_ID" 1m30s 2m45s
```

**Custom output directory:**
```bash
python yt2mp3/yt_to_mp3.py "https://youtube.com/watch?v=VIDEO_ID" -o ~/Music
```

**Verbose mode (debug):**
```bash
python yt2mp3/yt_to_mp3.py "https://youtube.com/watch?v=VIDEO_ID" -v
```

### 📖 Usage

```
usage: yt_to_mp3.py [-h] [-o OUTPUT_DIR] [-q QUALITY] [--min-duration MIN_DURATION] 
                    [-v] [--no-cache] url [start_time] [end_time]

Convert a YouTube video (or trimmed section) to high-quality MP3 with metadata 
embedding and intelligent caching.

positional arguments:
  url                   YouTube video URL
  start_time            Optional start time (e.g., 1m3s, 1h0m5s)
  end_time              Optional end time (e.g., 2m15s, 1h10m0s)

optional arguments:
  -h, --help            Show this help message and exit
  -o, --output-dir DIR  Output directory (default: current directory)
  -q, --quality QUALITY Audio quality (default: 320K)
  --min-duration SEC    Minimum clip duration in seconds (default: 5)
  -v, --verbose         Enable verbose/debug logging
  --no-cache            Disable caching, always re-download source audio
```

### 📁 Output Files

Files are written to the specified output directory (or script directory by default):

- **Full video:** `<title>__full.mp3`
- **Trimmed clip:** `<title>__HH-MM-SS__HH-MM-SS.mp3`

### 🎯 Time Format Examples

| Format | Example | Meaning |
|--------|---------|---------|
| Seconds only | `30s` | 30 seconds |
| Minutes + seconds | `2m15s` | 2 minutes, 15 seconds |
| Hours + minutes + seconds | `1h30m0s` | 1 hour, 30 minutes |
| Minutes only | `5m` | 5 minutes |
| Hours only | `2h` | 2 hours |

### ⚠️ Important Notes

- **Playlist URLs are not supported** - Only single video URLs work
- **Minimum duration** - Clips must be at least 5 seconds (configurable)
- **Cache location** - Cached files stored in `yt2mp3/.cache/`
- **Region restrictions** - Some videos may be unavailable in certain countries

---

## 🧪 Testing

Run unit tests with pytest:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=yt2mp3 --cov-report=html
```

---

## 🛠 Development

### Code Quality

```bash
# Format code
black yt2mp3/ tests/

# Lint
flake8 yt2mp3/ tests/

# Type checking
mypy yt2mp3/
```

### Project Structure

```
utils/
├── yt2mp3/
│   ├── yt_to_mp3.py      # Main conversion script
│   └── .cache/           # Cached source audio (gitignored)
├── tests/
│   └── test_yt_to_mp3.py # Unit tests
├── setup.sh              # Linux/macOS setup script
├── setup.bat             # Windows setup script
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- **yt-dlp** - YouTube download engine
- **ffmpeg** - Audio processing and encoding
- **Contributors** - Thanks to everyone who improves this project!

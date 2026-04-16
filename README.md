# utils

## `yt2mp3`

`yt2mp3/yt_to_mp3.py` downloads audio from a YouTube video and exports it as a high-quality MP3. It supports full-video exports and trimmed clips, and it caches the source audio per YouTube video ID so multiple trims from the same link do not trigger repeated downloads.

### Prerequisites

Make sure these are installed and available in your `PATH`:

- `python` 3
- `yt-dlp`
- `ffmpeg`

### Usage

Run the script from the repository root:

```powershell
python .\yt2mp3\yt_to_mp3.py "<youtube-url>"
```

Export only a section of the video:

```powershell
python .\yt2mp3\yt_to_mp3.py "<youtube-url>" 1m07s 2m00s
```

Output files are written to `yt2mp3/`:

- Full video: `<title>__full.mp3`
- Trimmed clip: `<title>__HH-MM-SS__HH-MM-SS.mp3`

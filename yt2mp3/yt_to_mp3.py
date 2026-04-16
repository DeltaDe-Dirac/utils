#!/usr/bin/env python3
"""
YouTube to MP3 Converter with trimming support.

Converts YouTube videos to high-quality MP3 files with optional time trimming,
metadata embedding, and intelligent caching.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Type Definitions
# ─────────────────────────────────────────────────────────────────────────────


class VideoInfo(TypedDict):
    """Metadata about a YouTube video."""

    id: str
    title: str
    duration: int
    uploader: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Constants & Configuration
# ─────────────────────────────────────────────────────────────────────────────

TIME_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)
FILENAME_SAFE_CHARS_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")
PLAYLIST_PATTERNS = [r"&list=", r"/playlist\?", r"&playlist="]

# Configurable via environment or args
DEFAULT_MIN_DURATION_SECONDS = 5
DEFAULT_AUDIO_QUALITY = "320K"


# ─────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────────────────────


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────────────
# Error Handling
# ─────────────────────────────────────────────────────────────────────────────


class ConversionError(Exception):
    """Custom exception for conversion failures."""

    pass


def fail(message: str, exit_code: int = 1) -> None:
    """Log error and exit with specified code."""
    logger.error(message)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# Time Parsing Utilities
# ─────────────────────────────────────────────────────────────────────────────


def parse_time_to_seconds(value: Optional[str], label: str) -> Optional[int]:
    """
    Parse time string (e.g., '1h30m5s', '2m15s', '45s') to seconds.

    Args:
        value: Time string or None
        label: Description for error messages (e.g., 'start time')

    Returns:
        Total seconds or None if value is None

    Raises:
        SystemExit: If format is invalid
    """
    if value is None:
        return None

    time_value = value.strip()
    if not time_value:
        fail(f"{label} is empty. Expected format like '1m3s' or '1h0m5s'.")

    match = TIME_PATTERN.fullmatch(time_value)
    if not match:
        fail(
            f"Invalid {label} '{value}'. Expected non-negative format like "
            "'1m3s', '1h0m5s', or '45s'."
        )

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)

    if hours == 0 and minutes == 0 and seconds == 0:
        return 0

    return hours * 3600 + minutes * 60 + seconds


def parse_duration_to_seconds(duration: str) -> int:
    """
    Parse duration string from yt-dlp (supports 'HH:MM:SS' or seconds).

    Args:
        duration: Duration string from yt-dlp metadata

    Returns:
        Total seconds as integer

    Raises:
        SystemExit: If parsing fails
    """
    value = duration.strip()
    if not value:
        fail("Unable to read video duration from yt-dlp output.")

    # Handle plain seconds (int or float)
    if ":" not in value:
        try:
            return int(float(value))
        except ValueError:
            fail(f"Unable to parse video duration '{value}'.")

    # Handle HH:MM:SS or MM:SS format
    parts = value.split(":")
    if len(parts) > 3:
        fail(f"Unsupported duration format from yt-dlp: '{value}'.")

    try:
        seconds = float(parts[-1])
        minutes = int(parts[-2]) if len(parts) >= 2 else 0
        hours = int(parts[-3]) if len(parts) == 3 else 0
    except ValueError:
        fail(f"Unable to parse video duration '{value}'.")

    return int(hours * 3600 + minutes * 60 + seconds)


def to_timestamp(total_seconds: int) -> str:
    """Convert seconds to HH:MM:SS timestamp format."""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def to_filename_timestamp(total_seconds: int) -> str:
    """Convert seconds to filename-safe timestamp (HH-MM-SS)."""
    return to_timestamp(total_seconds).replace(":", "-")


# ─────────────────────────────────────────────────────────────────────────────
# Dependency Management
# ─────────────────────────────────────────────────────────────────────────────


def check_dependencies() -> None:
    """Verify required binaries are available in PATH."""
    missing = []
    for binary in ("yt-dlp", "ffmpeg"):
        if shutil.which(binary) is None:
            missing.append(binary)

    if missing:
        fail(
            f"Required dependencies not found: {', '.join(missing)}\n"
            f"Please run the setup script first:\n"
            f"  - Linux/macOS: ./setup.sh\n"
            f"  - Windows: setup.bat"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Playlist Detection
# ─────────────────────────────────────────────────────────────────────────────


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist (not a single video)."""
    return any(re.search(pattern, url) for pattern in PLAYLIST_PATTERNS)


# ─────────────────────────────────────────────────────────────────────────────
# Filename Sanitization
# ─────────────────────────────────────────────────────────────────────────────


def sanitize_filename(value: str) -> str:
    """
    Sanitize string for use in filenames.

    Removes special characters, normalizes whitespace, and ensures
    the filename is valid across platforms.
    """
    cleaned = FILENAME_SAFE_CHARS_PATTERN.sub("", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.rstrip(". ") or "youtube_audio"


# ─────────────────────────────────────────────────────────────────────────────
# Video Metadata Retrieval
# ─────────────────────────────────────────────────────────────────────────────


def get_video_info(url: str) -> VideoInfo:
    """
    Fetch video metadata from YouTube using yt-dlp.

    Args:
        url: YouTube video URL

    Returns:
        VideoInfo dict with id, title, duration, and uploader

    Raises:
        SystemExit: If metadata fetch fails
    """
    logger.debug("Fetching video metadata from YouTube...")
    result = subprocess.run(
        [
            "yt-dlp",
            "--no-warnings",
            "--dump-single-json",
            "--no-playlist",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        # Provide helpful context based on error content
        if "private video" in stderr.lower():
            fail(
                "This video is private or requires authentication.\n"
                "Please ensure the video is public or you have access."
            )
        elif "unavailable" in stderr.lower():
            fail(
                "This video is unavailable. Possible reasons:\n"
                "  - Video was deleted or made private\n"
                "  - Region-locked in your location\n"
                "  - URL is incorrect"
            )
        elif "copyright" in stderr.lower():
            fail(
                "This video has copyright restrictions preventing download.\n"
                "Please respect content creators' rights."
            )
        else:
            fail(f"Failed to fetch video metadata: {stderr}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Failed to parse yt-dlp metadata output: {exc}")

    video_id = str(payload.get("id") or "").strip()
    title = str(payload.get("title") or "").strip()
    uploader = payload.get("uploader") or payload.get("channel")
    duration_value = payload.get("duration")

    if not video_id:
        fail("yt-dlp metadata did not include a video ID.")
    if not title:
        fail("yt-dlp metadata did not include a title.")

    # Parse duration (can be int, float, or string)
    if isinstance(duration_value, (int, float)):
        duration = int(duration_value)
    else:
        duration_text = str(duration_value or payload.get("duration_string") or "").strip()
        duration = parse_duration_to_seconds(duration_text)

    logger.info(f"Found video: '{title}' ({to_timestamp(duration)})")

    return {"id": video_id, "title": title, "duration": duration, "uploader": uploader}


# ─────────────────────────────────────────────────────────────────────────────
# Range Validation
# ─────────────────────────────────────────────────────────────────────────────


def validate_range(start: int, end: int, duration: int, min_duration: int) -> None:
    """
    Validate trim range against video duration.

    Args:
        start: Start time in seconds
        end: End time in seconds
        duration: Total video duration in seconds
        min_duration: Minimum allowed clip duration

    Raises:
        SystemExit: If validation fails
    """
    if start < 0 or end < 0:
        fail("Time values cannot be negative.")
    if start > duration:
        fail(
            f"Start time ({start}s) exceeds video length ({duration}s).\n"
            f"Video duration: {to_timestamp(duration)}"
        )
    if end > duration:
        fail(
            f"End time ({end}s) exceeds video length ({duration}s).\n"
            f"Video duration: {to_timestamp(duration)}"
        )
    if start > end:
        fail(
            f"Start time ({start}s) cannot be greater than end time ({end}s)."
        )

    clip_duration = end - start
    if clip_duration < min_duration:
        fail(
            f"Selected duration ({clip_duration}s) is too short.\n"
            f"Minimum required: {min_duration} seconds"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Argument Parsing
# ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build and configure argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert a YouTube video (or trimmed section) to high-quality MP3 "
            "with metadata embedding and intelligent caching."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://youtube.com/watch?v=..."                    # Full video
  %(prog)s "https://youtube.com/watch?v=..." 1m30s 2m45s        # Trimmed clip
  %(prog)s "https://youtube.com/watch?v=..." -o ~/Music         # Custom output
  %(prog)s "https://youtube.com/watch?v=..." -v                 # Verbose mode
        """,
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "start_time",
        nargs="?",
        default=None,
        help="Optional start time (e.g., 1m3s, 1h0m5s)",
    )
    parser.add_argument(
        "end_time",
        nargs="?",
        default=None,
        help="Optional end time (e.g., 2m15s, 1h10m0s)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=str,
        default=DEFAULT_AUDIO_QUALITY,
        help=f"Audio quality (default: {DEFAULT_AUDIO_QUALITY})",
    )
    parser.add_argument(
        "--min-duration",
        type=int,
        default=DEFAULT_MIN_DURATION_SECONDS,
        help=f"Minimum clip duration in seconds (default: {DEFAULT_MIN_DURATION_SECONDS})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching, always re-download source audio",
    )
    return parser


# ─────────────────────────────────────────────────────────────────────────────
# Output Path Building
# ─────────────────────────────────────────────────────────────────────────────


def build_output_path(
    output_dir: Path, title: str, start: int, end: int, duration: int
) -> Path:
    """
    Build output filename based on title and trim range.

    Args:
        output_dir: Target directory
        title: Video title
        start: Start time in seconds
        end: End time in seconds
        duration: Total video duration

    Returns:
        Full path to output MP3 file
    """
    safe_title = sanitize_filename(title)
    if start == 0 and end == duration:
        suffix = "full"
    else:
        suffix = f"{to_filename_timestamp(start)}__{to_filename_timestamp(end)}"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir / f"{safe_title}__{suffix}.mp3"


# ─────────────────────────────────────────────────────────────────────────────
# Cache Management
# ─────────────────────────────────────────────────────────────────────────────


def resolve_cached_source_path(cache_dir: Path, video_id: str) -> Optional[Path]:
    """Find cached source audio file for video ID."""
    matches = sorted(path for path in cache_dir.glob(f"{video_id}.*") if path.is_file())
    return matches[0] if matches else None


def download_source_audio(
    url: str, cache_dir: Path, video_id: str, no_cache: bool = False
) -> Path:
    """
    Download source audio from YouTube with caching support.

    Args:
        url: YouTube video URL
        cache_dir: Directory for cached files
        video_id: YouTube video ID
        no_cache: If True, skip cache and re-download

    Returns:
        Path to downloaded (or cached) audio file

    Raises:
        SystemExit: If download fails
    """
    # Check cache first
    if not no_cache:
        existing = resolve_cached_source_path(cache_dir, video_id)
        if existing is not None:
            logger.info(f"✓ Using cached source audio: {existing.name}")
            return existing

    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(cache_dir / f"{video_id}.%(ext)s")

    # Build yt-dlp command with progress bar
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--progress",
        "--newline",  # Progress on new lines
        "-f",
        "bestaudio/best",
        "-o",
        output_template,
        url,
    ]

    logger.info("Downloading source audio from YouTube...")
    logger.debug(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        fail(
            "Source audio download failed.\n"
            "Common causes:\n"
            "  - Invalid or expired URL\n"
            "  - Video is private/unavailable\n"
            "  - Network connectivity issues\n"
            "  - yt-dlp needs update (run: pip install -U yt-dlp)"
        )

    # Verify download succeeded
    downloaded = resolve_cached_source_path(cache_dir, video_id)
    if downloaded is None:
        fail(
            "yt-dlp completed, but cached source audio file was not found.\n"
            "This may indicate a download failure or filesystem issue."
        )

    logger.info(f"✓ Download complete: {downloaded.name}")
    return downloaded


# ─────────────────────────────────────────────────────────────────────────────
# MP3 Export with Metadata
# ─────────────────────────────────────────────────────────────────────────────


def export_mp3(
    source_path: Path,
    output_path: Path,
    start: int,
    end: int,
    title: str,
    uploader: Optional[str] = None,
    quality: str = DEFAULT_AUDIO_QUALITY,
) -> None:
    """
    Export trimmed audio as MP3 with embedded metadata.

    Args:
        source_path: Path to source audio file
        output_path: Path for output MP3
        start: Start time in seconds
        end: End time in seconds
        title: Track title
        uploader: Artist/uploader name (optional)
        quality: Audio quality (e.g., '320K')

    Raises:
        SystemExit: If export fails
    """
    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-t",
        str(end - start),
        "-i",
        str(source_path),
        "-vn",  # No video
        "-codec:a",
        "libmp3lame",
        "-b:a",
        quality,
        "-metadata",
        f"title={title}",
    ]

    # Add artist metadata if available
    if uploader:
        cmd.extend(["-metadata", f"artist={uploader}"])

    cmd.append(str(output_path))

    logger.info(f"Exporting MP3: {output_path.name}")
    logger.debug(f"Quality: {quality}, Duration: {to_timestamp(end - start)}")

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        error_details = result.stderr.strip() or "unknown error"
        fail(
            f"MP3 export failed: {error_details}\n"
            "Possible causes:\n"
            "  - Source file corrupted\n"
            "  - Invalid trim range\n"
            "  - ffmpeg installation issue"
        )

    logger.info(f"✓ Export complete: {output_path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Main entry point for YouTube to MP3 conversion."""
    parser = build_parser()
    args = parser.parse_args()

    # Configure logging based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    # Check dependencies
    check_dependencies()

    # Check for playlist URLs
    if is_playlist_url(args.url):
        logger.warning(
            "⚠️  Playlist URL detected. This tool only supports single videos.\n"
            "Please provide a direct video URL (not a playlist).\n"
            "Example: https://youtube.com/watch?v=VIDEO_ID"
        )
        fail("Playlist URLs are not supported. Exiting.", exit_code=2)

    # Parse time arguments
    start_arg = parse_time_to_seconds(args.start_time, "start time")
    end_arg = parse_time_to_seconds(args.end_time, "end time")

    # Fetch video metadata
    video_info = get_video_info(args.url)
    duration = int(video_info["duration"])

    # Validate minimum duration for full video
    if start_arg is None and end_arg is None and duration < args.min_duration:
        fail(
            f"Video duration ({duration}s) is shorter than minimum required "
            f"({args.min_duration}s)."
        )

    # Set default range if not specified
    start = 0 if start_arg is None else start_arg
    end = duration if end_arg is None else end_arg

    # Validate trim range
    validate_range(start, end, duration, args.min_duration)

    # Build paths
    script_dir = Path(__file__).resolve().parent
    cache_dir = script_dir / ".cache"

    output_path = build_output_path(
        args.output_dir,
        str(video_info["title"]),
        start,
        end,
        duration,
    )

    # Download (or retrieve cached) source audio
    source_path = download_source_audio(
        args.url, cache_dir, str(video_info["id"]), no_cache=args.no_cache
    )

    # Export MP3 with metadata
    export_mp3(
        source_path,
        output_path,
        start,
        end,
        str(video_info["title"]),
        video_info.get("uploader"),
        args.quality,
    )

    # Success message
    logger.info(
        f"\n{'='*60}\n"
        f"✓ Successfully converted to MP3!\n"
        f"{'='*60}\n"
        f"Output: {output_path}\n"
        f"Duration: {to_timestamp(end - start)}\n"
        f"Quality: {args.quality}\n"
        f"{'='*60}"
    )


if __name__ == "__main__":
    main()

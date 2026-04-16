#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TIME_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)
MIN_DURATION_SECONDS = 5
FILENAME_SAFE_CHARS_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def parse_time_to_seconds(value: str | None, label: str) -> int | None:
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
    value = duration.strip()
    if not value:
        fail("Unable to read video duration from yt-dlp output.")

    if ":" not in value:
        try:
            return int(float(value))
        except ValueError:
            fail(f"Unable to parse video duration '{value}'.")

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
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def to_filename_timestamp(total_seconds: int) -> str:
    return to_timestamp(total_seconds).replace(":", "-")


def check_dependencies() -> None:
    for binary in ("yt-dlp", "ffmpeg"):
        if shutil.which(binary) is None:
            fail(f"Required dependency '{binary}' is not installed or not in PATH.")


def sanitize_filename(value: str) -> str:
    cleaned = FILENAME_SAFE_CHARS_PATTERN.sub("", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.rstrip(". ") or "youtube_audio"


def get_video_info(url: str) -> dict[str, str | int]:
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
        fail(f"Failed to fetch video metadata via yt-dlp: {stderr}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Failed to parse yt-dlp metadata output: {exc}")

    video_id = str(payload.get("id") or "").strip()
    title = str(payload.get("title") or "").strip()
    duration_value = payload.get("duration")

    if not video_id:
        fail("yt-dlp metadata did not include a video ID.")
    if not title:
        fail("yt-dlp metadata did not include a title.")

    if isinstance(duration_value, (int, float)):
        duration = int(duration_value)
    else:
        duration_text = str(duration_value or payload.get("duration_string") or "").strip()
        duration = parse_duration_to_seconds(duration_text)

    return {"id": video_id, "title": title, "duration": duration}


def validate_range(start: int, end: int, duration: int) -> None:
    if start < 0 or end < 0:
        fail("Time values cannot be negative.")
    if start > duration:
        fail(f"Start time ({start}s) cannot be greater than clip length ({duration}s).")
    if end > duration:
        fail(f"End time ({end}s) cannot be greater than clip length ({duration}s).")
    if start > end:
        fail("Start time cannot be greater than end time.")
    if (end - start) < MIN_DURATION_SECONDS:
        fail(
            f"Selected duration must be at least {MIN_DURATION_SECONDS} seconds "
            f"(current: {end - start}s)."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a YouTube video (or a trimmed section) to high-quality MP3 "
            "in the script directory."
        )
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "start_time",
        nargs="?",
        default=None,
        help="Optional start time (e.g. 1m3s, 1h0m5s)",
    )
    parser.add_argument(
        "end_time",
        nargs="?",
        default=None,
        help="Optional end time (e.g. 2m15s, 1h10m0s)",
    )
    return parser


def build_output_path(script_dir: Path, title: str, start: int, end: int, duration: int) -> Path:
    safe_title = sanitize_filename(title)
    if start == 0 and end == duration:
        suffix = "full"
    else:
        suffix = f"{to_filename_timestamp(start)}__{to_filename_timestamp(end)}"
    return script_dir / f"{safe_title}__{suffix}.mp3"


def resolve_cached_source_path(cache_dir: Path, video_id: str) -> Path | None:
    matches = sorted(path for path in cache_dir.glob(f"{video_id}.*") if path.is_file())
    return matches[0] if matches else None


def download_source_audio(url: str, cache_dir: Path, video_id: str) -> Path:
    existing = resolve_cached_source_path(cache_dir, video_id)
    if existing is not None:
        print(f"Using cached source audio: {existing.name}")
        return existing

    cache_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(cache_dir / f"{video_id}.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-o",
        output_template,
        url,
    ]

    print("Downloading source audio to cache...")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        fail("Source audio download failed. Check yt-dlp output above for details.")

    downloaded = resolve_cached_source_path(cache_dir, video_id)
    if downloaded is None:
        fail("yt-dlp completed, but the cached source audio file was not found.")

    return downloaded


def export_mp3(source_path: Path, output_path: Path, start: int, end: int, title: str) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-t",
        str(end - start),
        "-i",
        str(source_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "0",
        "-metadata",
        f"title={title}",
        str(output_path),
    ]

    print(f"Exporting MP3: {output_path.name}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        fail("MP3 export failed. Check ffmpeg output above for details.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    check_dependencies()

    start_arg = parse_time_to_seconds(args.start_time, "start time")
    end_arg = parse_time_to_seconds(args.end_time, "end time")
    video_info = get_video_info(args.url)
    duration = int(video_info["duration"])

    if start_arg is None and end_arg is None and duration < MIN_DURATION_SECONDS:
        fail(
            f"Clip duration is {duration}s, but at least "
            f"{MIN_DURATION_SECONDS}s is required."
        )

    start = 0 if start_arg is None else start_arg
    end = duration if end_arg is None else end_arg
    validate_range(start, end, duration)

    script_dir = Path(__file__).resolve().parent
    cache_dir = script_dir / ".cache"
    output_path = build_output_path(
        script_dir,
        str(video_info["title"]),
        start,
        end,
        duration,
    )
    source_path = download_source_audio(args.url, cache_dir, str(video_info["id"]))
    export_mp3(source_path, output_path, start, end, str(video_info["title"]))

    print(f"Successfully converted to MP3: {output_path.name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

TIME_PATTERN = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)
MIN_DURATION_SECONDS = 5


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


def check_dependencies() -> None:
    for binary in ("yt-dlp", "ffmpeg"):
        if shutil.which(binary) is None:
            fail(f"Required dependency '{binary}' is not installed or not in PATH.")


def get_video_duration(url: str) -> int:
    result = subprocess.run(
        ["yt-dlp", "--no-warnings", "--get-duration", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        fail(f"Failed to fetch video duration via yt-dlp: {stderr}")

    return parse_duration_to_seconds(result.stdout)


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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    check_dependencies()

    start_arg = parse_time_to_seconds(args.start_time, "start time")
    end_arg = parse_time_to_seconds(args.end_time, "end time")
    duration = get_video_duration(args.url)

    if start_arg is None and end_arg is None and duration < MIN_DURATION_SECONDS:
        fail(
            f"Clip duration is {duration}s, but at least "
            f"{MIN_DURATION_SECONDS}s is required."
        )

    start = 0 if start_arg is None else start_arg
    end = duration if end_arg is None else end_arg
    validate_range(start, end, duration)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_template = os.path.join(script_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--embed-metadata",
        "-o",
        output_template,
    ]

    if args.start_time is not None or args.end_time is not None:
        start_ts = to_timestamp(start) if args.start_time is not None else ""
        end_ts = to_timestamp(end) if args.end_time is not None else ""
        cmd.extend(["--download-sections", f"*{start_ts}-{end_ts}"])

    cmd.append(args.url)

    action = "full video" if (args.start_time is None and args.end_time is None) else "trimmed section"
    print(f"Downloading {action} and converting to MP3...")

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        fail("Conversion failed. Check yt-dlp/ffmpeg output above for details.")

    print("Successfully converted to MP3.")


if __name__ == "__main__":
    main()

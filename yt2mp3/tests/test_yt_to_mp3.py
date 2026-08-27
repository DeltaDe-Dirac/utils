#!/usr/bin/env python3
"""
Unit tests for yt2mp3 utility.

Run with: pytest tests/test_yt_to_mp3.py -v
"""
import os
import time

import pytest
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions to test
# Note: We import specific functions to avoid side effects from main()
import importlib.util

# Load the module dynamically from the package root (not tests/).
_MODULE_PATH = Path(__file__).resolve().parent.parent / "yt_to_mp3.py"
spec = importlib.util.spec_from_file_location("yt_to_mp3", _MODULE_PATH)
yt_to_mp3 = importlib.util.module_from_spec(spec)
sys.modules["yt_to_mp3"] = yt_to_mp3
spec.loader.exec_module(yt_to_mp3)


# ─────────────────────────────────────────────────────────────────────────────
# Time Parsing Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestTimeParsing:
    """Test time string parsing functions."""

    def test_parse_seconds_only(self):
        """Parse simple seconds format."""
        # Access the function from the loaded module
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func("30s", "test") == 30
            assert func("45s", "test") == 45
            assert func("0s", "test") == 0

    def test_parse_minutes_seconds(self):
        """Parse minutes and seconds format."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func("1m30s", "test") == 90
            assert func("2m0s", "test") == 120
            assert func("5m45s", "test") == 345

    def test_parse_hours_minutes_seconds(self):
        """Parse hours, minutes, and seconds format."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func("1h0m0s", "test") == 3600
            assert func("1h30m0s", "test") == 5400
            assert func("2h15m30s", "test") == 8130

    def test_parse_minutes_only(self):
        """Parse minutes only format."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func("1m", "test") == 60
            assert func("10m", "test") == 600

    def test_parse_hours_only(self):
        """Parse hours only format."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func("1h", "test") == 3600
            assert func("2h", "test") == 7200

    def test_parse_none_value(self):
        """Handle None input gracefully."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            assert func(None, "test") is None

    def test_parse_invalid_format(self):
        """Reject invalid time formats."""
        func = getattr(yt_to_mp3, 'parse_time_to_seconds', None)
        if func:
            with pytest.raises(SystemExit):
                func("invalid", "test")
            with pytest.raises(SystemExit):
                func("1:30", "test")
            with pytest.raises(SystemExit):
                func("abc", "test")


# ─────────────────────────────────────────────────────────────────────────────
# Duration Parsing Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestDurationParsing:
    """Test duration string parsing from yt-dlp."""

    def test_parse_colon_format_mm_ss(self):
        """Parse MM:SS format."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            assert func("3:30") == 210
            assert func("10:00") == 600
            assert func("0:45") == 45

    def test_parse_colon_format_hh_mm_ss(self):
        """Parse HH:MM:SS format."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            assert func("1:30:00") == 5400
            assert func("2:15:30") == 8130

    def test_parse_plain_seconds(self):
        """Parse plain seconds as string."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            assert func("180") == 180
            assert func("300") == 300

    def test_parse_plain_seconds_float(self):
        """Parse plain seconds as float string."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            assert func("180.5") == 180
            assert func("300.9") == 300

    def test_parse_empty_string(self):
        """Reject empty duration string."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            with pytest.raises(SystemExit):
                func("")

    def test_parse_invalid_format(self):
        """Reject invalid duration formats."""
        func = getattr(yt_to_mp3, 'parse_duration_to_seconds', None)
        if func:
            with pytest.raises(SystemExit):
                func("invalid")


# ─────────────────────────────────────────────────────────────────────────────
# Timestamp Conversion Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestTimestampConversion:
    """Test timestamp conversion functions."""

    def test_to_timestamp_seconds(self):
        """Convert seconds to timestamp."""
        func = getattr(yt_to_mp3, 'to_timestamp', None)
        if func:
            assert func(0) == "00:00:00"
            assert func(30) == "00:00:30"
            assert func(90) == "00:01:30"
            assert func(3661) == "01:01:01"

    def test_to_filename_timestamp(self):
        """Convert seconds to filename-safe timestamp."""
        func = getattr(yt_to_mp3, 'to_filename_timestamp', None)
        if func:
            assert func(0) == "00-00-00"
            assert func(90) == "00-01-30"
            assert func(3661) == "01-01-01"


# ─────────────────────────────────────────────────────────────────────────────
# Filename Sanitization Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_sanitize_clean_title(self):
        """Keep clean titles unchanged."""
        func = getattr(yt_to_mp3, 'sanitize_filename', None)
        if func:
            assert func("My Video Title") == "My Video Title"
            assert func("Song Name") == "Song Name"

    def test_sanitize_special_chars(self):
        """Remove special characters."""
        func = getattr(yt_to_mp3, 'sanitize_filename', None)
        if func:
            assert "My Video" in func("My Video @#$%^&*!")
            assert "Song" in func("Song [Official Music Video]")

    def test_sanitize_unicode(self):
        """Handle unicode characters."""
        func = getattr(yt_to_mp3, 'sanitize_filename', None)
        if func:
            # Should keep basic unicode letters
            result = func("Música Española")
            assert "Música" in result or "Msica" in result

    def test_sanitize_empty_result(self):
        """Provide default for empty result."""
        func = getattr(yt_to_mp3, 'sanitize_filename', None)
        if func:
            assert func("@#$%") == "youtube_audio"

    def test_sanitize_whitespace(self):
        """Normalize whitespace."""
        func = getattr(yt_to_mp3, 'sanitize_filename', None)
        if func:
            assert func("My   Video    Title") == "My Video Title"


# ─────────────────────────────────────────────────────────────────────────────
# Playlist Detection Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPlaylistDetection:
    """Test playlist URL detection."""

    def test_is_video_url(self):
        """Detect regular video URLs."""
        func = getattr(yt_to_mp3, 'is_playlist_url', None)
        if func:
            assert func("https://youtube.com/watch?v=abc123") is False
            assert func("https://youtu.be/abc123") is False

    def test_is_playlist_url_with_list_param(self):
        """Detect playlist URLs with &list= parameter."""
        func = getattr(yt_to_mp3, 'is_playlist_url', None)
        if func:
            assert func("https://youtube.com/watch?v=abc123&list=PLxyz") is True
            assert func("https://youtube.com/watch?v=abc123&list=PLxyz&index=5") is True

    def test_is_playlist_url_explicit(self):
        """Detect explicit playlist URLs."""
        func = getattr(yt_to_mp3, 'is_playlist_url', None)
        if func:
            assert func("https://youtube.com/playlist?list=PLxyz") is True


# ─────────────────────────────────────────────────────────────────────────────
# Range Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRangeValidation:
    """Test time range validation."""

    def test_valid_range(self):
        """Accept valid time ranges."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            # Should not raise
            func(0, 60, 120, 5)
            func(30, 90, 120, 5)

    def test_negative_start(self):
        """Reject negative start time."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            with pytest.raises(SystemExit):
                func(-1, 60, 120, 5)

    def test_start_exceeds_duration(self):
        """Reject start time exceeding duration."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            with pytest.raises(SystemExit):
                func(150, 180, 120, 5)

    def test_end_exceeds_duration(self):
        """Reject end time exceeding duration."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            with pytest.raises(SystemExit):
                func(30, 150, 120, 5)

    def test_start_greater_than_end(self):
        """Reject start > end."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            with pytest.raises(SystemExit):
                func(90, 30, 120, 5)

    def test_duration_too_short(self):
        """Reject clips shorter than minimum."""
        func = getattr(yt_to_mp3, 'validate_range', None)
        if func:
            with pytest.raises(SystemExit):
                func(0, 3, 120, 5)  # 3 seconds < 5 second minimum


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests (Mocked)
# ─────────────────────────────────────────────────────────────────────────────


class TestIntegration:
    """Integration tests with mocked external dependencies."""

    @patch('yt_to_mp3.shutil.which')
    def test_check_dependencies_success(self, mock_which):
        """Pass when all dependencies are available."""
        mock_which.return_value = "/usr/bin/fake"
        func = getattr(yt_to_mp3, 'check_dependencies', None)
        if func:
            # Should not raise
            func()

    @patch('yt_to_mp3.shutil.which')
    def test_check_dependencies_missing(self, mock_which):
        """Fail when dependencies are missing."""
        mock_which.side_effect = lambda x: None if x == "yt-dlp" else "/usr/bin/fake"
        func = getattr(yt_to_mp3, 'check_dependencies', None)
        if func:
            with pytest.raises(SystemExit):
                func()


# ─────────────────────────────────────────────────────────────────────────────
# Cache size parsing
# ─────────────────────────────────────────────────────────────────────────────


class TestParseCacheMaxSize:
    """Parse --cache-max-size human sizes and raw bytes."""

    def test_parse_raw_bytes(self):
        assert yt_to_mp3.parse_cache_max_size("1024") == 1024
        assert yt_to_mp3.parse_cache_max_size("0") == 0

    def test_parse_mebibyte_suffix(self):
        assert yt_to_mp3.parse_cache_max_size("50M") == 50 * 1024**2
        assert yt_to_mp3.parse_cache_max_size("5m") == 5 * 1024**2

    def test_parse_gibibyte_suffix(self):
        assert yt_to_mp3.parse_cache_max_size("3G") == 3 * 1024**3
        assert yt_to_mp3.parse_cache_max_size("1g") == 1024**3

    def test_parse_kibibyte_suffix(self):
        assert yt_to_mp3.parse_cache_max_size("2K") == 2 * 1024

    def test_reject_invalid_size(self):
        with pytest.raises(ValueError):
            yt_to_mp3.parse_cache_max_size("abc")
        with pytest.raises(ValueError):
            yt_to_mp3.parse_cache_max_size("-1")
        with pytest.raises(ValueError):
            yt_to_mp3.parse_cache_max_size("3T")

    def test_default_cache_cap_is_3_gib(self):
        assert yt_to_mp3.DEFAULT_CACHE_MAX_SIZE == 3 * 1024**3


# ─────────────────────────────────────────────────────────────────────────────
# Cache pruning
# ─────────────────────────────────────────────────────────────────────────────


def _write_sized_file(path: Path, size: int, mtime: float) -> Path:
    path.write_bytes(b"x" * size)
    os.utime(path, (mtime, mtime))
    return path


def _cache_total_bytes(cache_dir: Path) -> int:
    return sum(p.stat().st_size for p in cache_dir.iterdir() if p.is_file())


class TestPruneCache:
    """Prune yt2mp3/.cache/ oldest-first until total size is <= cap."""

    def test_prune_deletes_oldest_keeps_newest_under_low_cap(self, tmp_path):
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        now = time.time()
        size = 2 * 1024 * 1024  # 2 MiB each
        oldest = _write_sized_file(cache_dir / "oldest.bin", size, now - 300)
        middle = _write_sized_file(cache_dir / "middle.bin", size, now - 200)
        newest = _write_sized_file(cache_dir / "newest.bin", size, now - 100)
        cap = 5 * 1024 * 1024  # 5 MiB — 6 MiB total, drop oldest

        yt_to_mp3.prune_cache(cache_dir, cap)

        assert not oldest.exists()
        assert middle.exists()
        assert newest.exists()
        assert _cache_total_bytes(cache_dir) <= cap

    def test_prune_keeps_current_job_file_until_last(self, tmp_path):
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        now = time.time()
        size = 2 * 1024 * 1024
        keep = _write_sized_file(cache_dir / "keep.bin", size, now - 300)
        other_old = _write_sized_file(cache_dir / "other_old.bin", size, now - 200)
        other_new = _write_sized_file(cache_dir / "other_new.bin", size, now - 100)
        cap = 3 * 1024 * 1024  # 3 MiB — must drop both others, keep current

        yt_to_mp3.prune_cache(cache_dir, cap, keep=keep)

        assert keep.exists()
        assert not other_old.exists()
        assert not other_new.exists()
        assert _cache_total_bytes(cache_dir) <= cap

    def test_prune_deletes_keep_last_when_it_alone_exceeds_cap(self, tmp_path):
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        now = time.time()
        keep = _write_sized_file(cache_dir / "huge.bin", 4 * 1024 * 1024, now - 300)
        other = _write_sized_file(cache_dir / "small.bin", 1 * 1024 * 1024, now - 100)
        cap = 2 * 1024 * 1024

        yt_to_mp3.prune_cache(cache_dir, cap, keep=keep)

        assert not keep.exists()
        assert not other.exists()
        assert _cache_total_bytes(cache_dir) <= cap

    def test_prune_does_not_delete_output_mp3s(self, tmp_path):
        cache_dir = tmp_path / ".cache"
        output_dir = tmp_path / "output"
        cache_dir.mkdir()
        output_dir.mkdir()
        now = time.time()
        cached = _write_sized_file(cache_dir / "old.bin", 3 * 1024 * 1024, now - 200)
        mp3 = _write_sized_file(output_dir / "song__full.mp3", 3 * 1024 * 1024, now - 300)
        cap = 1 * 1024 * 1024

        yt_to_mp3.prune_cache(cache_dir, cap)

        assert not cached.exists()
        assert mp3.exists()

    def test_prune_noop_when_already_under_cap(self, tmp_path):
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()
        now = time.time()
        kept = _write_sized_file(cache_dir / "small.bin", 512, now - 10)

        yt_to_mp3.prune_cache(cache_dir, 1024)

        assert kept.exists()

    def test_cli_accepts_cache_max_size_flag(self):
        parser = yt_to_mp3.build_parser()
        args = parser.parse_args(
            ["https://youtube.com/watch?v=abc", "--cache-max-size", "50M"]
        )
        assert args.cache_max_size == 50 * 1024**2

    def test_cli_default_cache_max_size_is_3_gib(self):
        parser = yt_to_mp3.build_parser()
        args = parser.parse_args(["https://youtube.com/watch?v=abc"])
        assert args.cache_max_size == 3 * 1024**3


# ─────────────────────────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

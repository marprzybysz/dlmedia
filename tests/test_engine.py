#!/usr/bin/env python3
"""Cross-platform tests for gui/engine.py — command building, bundled-tool resolution,
dependency check. Stdlib unittest only (no PySide6), so it runs on Linux/macOS/Windows.
Run: python -m unittest discover -s tests   (or: python tests/test_engine.py)
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "gui"))

from engine import build_command, is_spotify, missing_deps, tool_path  # noqa: E402

YT = "https://youtu.be/abc"
SPOT = "https://open.spotify.com/track/xyz"


class TestEngineYouTube(unittest.TestCase):
    def test_mp3_is_yt_dlp_audio_extract(self):
        cmd = build_command(YT, "mp3", "192", "/tmp/o")
        self.assertEqual(cmd[0], "yt-dlp")
        self.assertIn("-x", cmd)
        self.assertIn("--audio-format", cmd)
        self.assertIn("mp3", cmd)

    def test_mp3_quality_passed_as_K(self):
        self.assertIn("192K", build_command(YT, "mp3", "192", "/tmp/o"))
        self.assertIn("320K", build_command(YT, "mp3", "320", "/tmp/o"))

    def test_mp3_default_quality_is_320(self):
        self.assertIn("320K", build_command(YT, "mp3", "", "/tmp/o"))

    def test_mp4_best_selector(self):
        cmd = build_command(YT, "mp4", "best", "/tmp/o")
        self.assertIn("-f", cmd)
        self.assertIn("bestvideo+bestaudio/best", cmd)
        self.assertIn("--merge-output-format", cmd)
        self.assertIn("mp4", cmd)

    def test_mp4_default_quality_is_best(self):
        self.assertIn("bestvideo+bestaudio/best", build_command(YT, "mp4", "", "/tmp/o"))

    def test_mp4_capped_heights(self):
        for h in ("4320", "2160", "1440", "1080", "720", "480", "360"):
            with self.subTest(height=h):
                self.assertTrue(any(f"height<={h}" in a for a in build_command(YT, "mp4", h, "/tmp/o")))

    def test_mp4_4k_not_capped_to_h264_mp4(self):
        # The selector must NOT force [ext=mp4] (which silently caps 4K/8K at 1080p).
        cmd = build_command(YT, "mp4", "2160", "/tmp/o")
        self.assertTrue(any("height<=2160" in a for a in cmd))
        self.assertFalse(any("[ext=mp4]" in a for a in cmd))

    def test_output_template_uses_out_dir(self):
        cmd = build_command(YT, "mp3", "320", "/music/out")
        self.assertIn("-o", cmd)
        self.assertIn("/music/out/%(title)s.%(ext)s", cmd)

    def test_url_is_last_arg(self):
        self.assertEqual(build_command(YT, "mp4", "best", "/tmp/o")[-1], YT)

    def test_url_is_stripped(self):
        self.assertEqual(build_command("  " + YT + "  ", "mp4")[-1], YT)


class TestEngineSpotify(unittest.TestCase):
    def test_routes_to_spotdl(self):
        self.assertEqual(build_command(SPOT, "mp4", "", "/tmp/o")[0], "spotdl")

    def test_default_bitrate_320k(self):
        self.assertIn("320k", build_command(SPOT, "mp4", "", "/tmp/o"))

    def test_custom_bitrate(self):
        self.assertIn("128k", build_command(SPOT, "mp3", "128", "/tmp/o"))

    def test_output_template(self):
        cmd = build_command(SPOT, "mp3", "", "/m")
        self.assertIn("--output", cmd)
        self.assertTrue(any("{artist} - {title}" in a for a in cmd))

    def test_format_toggle_ignored_for_spotify(self):
        # mp4 vs mp3 must not change the spotdl command (Spotify is audio-only)
        self.assertEqual(build_command(SPOT, "mp4", "192", "/m"),
                         build_command(SPOT, "mp3", "192", "/m"))

    def test_spotify_link_short_domain(self):
        self.assertEqual(build_command("https://spotify.link/abc", "mp4")[0], "spotdl")


class TestEngineValidation(unittest.TestCase):
    def test_empty_url_raises(self):
        with self.assertRaises(ValueError):
            build_command("", "mp4")

    def test_whitespace_url_raises(self):
        with self.assertRaises(ValueError):
            build_command("   ", "mp4")

    def test_bad_format_raises(self):
        with self.assertRaises(ValueError):
            build_command(YT, "ogg")


class TestIsSpotify(unittest.TestCase):
    def test_positive(self):
        self.assertTrue(is_spotify("https://open.spotify.com/album/1"))
        self.assertTrue(is_spotify("https://spotify.link/xyz"))

    def test_negative(self):
        self.assertFalse(is_spotify(YT))
        self.assertFalse(is_spotify("https://soundcloud.com/x"))


class TestBundledTools(unittest.TestCase):
    """Windows-relevant: tool_path appends .exe and joins paths per-OS."""

    def _suffix(self):
        return ".exe" if os.name == "nt" else ""

    def test_tool_path_falls_back_to_name(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(tool_path("yt-dlp", tools_dir=d), "yt-dlp")

    def test_tool_path_uses_bundled(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "yt-dlp" + self._suffix())
            open(p, "w").close()
            self.assertEqual(tool_path("yt-dlp", tools_dir=d), p)

    def test_build_command_uses_bundled_tools_and_ffmpeg_location(self):
        with tempfile.TemporaryDirectory() as d:
            suf = self._suffix()
            for t in ("yt-dlp", "ffmpeg"):
                open(os.path.join(d, t + suf), "w").close()
            cmd = build_command("https://youtu.be/x", "mp4", "best", "/o", tools_dir=d)
            self.assertTrue(cmd[0].endswith("yt-dlp" + suf))
            self.assertIn("--ffmpeg-location", cmd)

    def test_missing_deps_sees_bundled(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "yt-dlp" + self._suffix()), "w").close()
            open(os.path.join(d, "ffmpeg" + self._suffix()), "w").close()
            # nothing on PATH, but both bundled → none missing
            self.assertEqual(missing_deps(spotify=False, which=lambda t: None, tools_dir=d), [])


class TestMissingDeps(unittest.TestCase):
    def test_none_missing(self):
        self.assertEqual(missing_deps(which=lambda t: "/usr/bin/" + t), [])

    def test_all_missing_no_spotify(self):
        self.assertEqual(missing_deps(spotify=False, which=lambda t: None), ["yt-dlp", "ffmpeg"])

    def test_spotify_adds_spotdl(self):
        self.assertEqual(missing_deps(spotify=True, which=lambda t: None),
                         ["yt-dlp", "ffmpeg", "spotdl"])

    def test_only_ffmpeg_missing(self):
        which = lambda t: None if t == "ffmpeg" else "/x/" + t  # noqa: E731
        self.assertEqual(missing_deps(spotify=True, which=which), ["ffmpeg"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for the GUI's Qt-free core: gui/engine.py and gui/i18n.py.

Standard-library unittest only (no PySide6, no pytest), so it runs anywhere.
Run directly (`python3 tests/test_gui.py`), via unittest
(`python3 -m unittest -v tests.test_gui`), or through `bash tests/run.sh`.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
LOCALES = os.path.join(ROOT, "locales")
sys.path.insert(0, os.path.join(ROOT, "gui"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from engine import build_command, is_spotify, missing_deps  # noqa: E402
import i18n  # noqa: E402
from i18n import Catalog, available_languages  # noqa: E402
from spotdl_filter import filter_file, parse_spec  # noqa: E402

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


class TestCatalog(unittest.TestCase):
    def test_loads_english(self):
        self.assertEqual(Catalog("en").t("btn_download"), "Download")

    def test_loads_polish(self):
        self.assertEqual(Catalog("pl").t("btn_download"), "Pobierz")

    def test_unknown_language_falls_back_to_en(self):
        c = Catalog("zz")
        self.assertEqual(c.lang, "en")
        self.assertEqual(c.t("btn_download"), "Download")

    def test_missing_key_returns_key(self):
        self.assertEqual(Catalog("en").t("does_not_exist"), "does_not_exist")

    def test_template_interpolation(self):
        out = Catalog("en").t("summary_spot", 3, 10)
        self.assertEqual(out, "Downloaded: 3 / 10")

    def test_template_wrong_arg_count_does_not_crash(self):
        # too few args -> return the template unformatted rather than raising
        out = Catalog("en").t("summary_spot", 3)
        self.assertIsInstance(out, str)

    def test_runtime_language_switch(self):
        c = Catalog("en")
        c.load("pl")
        self.assertEqual(c.t("btn_download"), "Pobierz")

    def test_gui_key_present(self):
        self.assertEqual(Catalog("en").t("gui_done"), "Done")
        self.assertEqual(Catalog("pl").t("gui_done"), "Gotowe")

    def test_locales_env_override(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "xx.json"), "w", encoding="utf-8") as f:
                json.dump({"btn_download": "ZZZ"}, f)
            old = os.environ.get("DLMEDIA_LOCALES")
            os.environ["DLMEDIA_LOCALES"] = d
            try:
                self.assertEqual(Catalog("xx").t("btn_download"), "ZZZ")
                self.assertIn("xx", available_languages())
            finally:
                if old is None:
                    del os.environ["DLMEDIA_LOCALES"]
                else:
                    os.environ["DLMEDIA_LOCALES"] = old


class TestSpotdlFilter(unittest.TestCase):
    def test_parse_pick_list(self):
        self.assertEqual(parse_spec("1,3,5", 8), [1, 3, 5])

    def test_parse_range(self):
        self.assertEqual(parse_spec("2-4,7", 8), [2, 3, 4, 7])

    def test_parse_dedupes_and_sorts(self):
        self.assertEqual(parse_spec("5,1-3,2", 8), [1, 2, 3, 5])

    def test_parse_clamps_out_of_range(self):
        self.assertEqual(parse_spec("5-99", 8), [5, 6, 7, 8])

    def test_parse_ignores_blanks(self):
        self.assertEqual(parse_spec("1,,3,", 8), [1, 3])

    def test_parse_bad_input_raises(self):
        with self.assertRaises(ValueError):
            parse_spec("abc", 8)

    def test_filter_file_writes_subset(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "all.spotdl")
            dst = os.path.join(d, "picked.spotdl")
            data = [{"artist": f"A{i}", "name": f"S{i}", "list_name": "Album"} for i in range(1, 9)]
            with open(src, "w") as f:
                json.dump(data, f)
            n = filter_file(src, "1,3,5", dst)
            self.assertEqual(n, 3)
            with open(dst) as f:
                picked = json.load(f)
            self.assertEqual([s["name"] for s in picked], ["S1", "S3", "S5"])
            self.assertEqual(picked[0]["list_name"], "Album")  # metadata preserved


class TestLocaleFiles(unittest.TestCase):
    def _load(self, lang):
        with open(os.path.join(LOCALES, f"{lang}.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_available_languages_sorted_and_complete(self):
        langs = available_languages()
        self.assertEqual(langs, sorted(langs))
        self.assertIn("pl", langs)
        self.assertIn("en", langs)

    def test_all_languages_have_identical_keys(self):
        base = None
        for lang in available_languages():
            keys = set(self._load(lang))
            if base is None:
                base = keys
            else:
                self.assertEqual(keys, base, f"{lang}.json key set differs")

    def test_every_file_is_valid_json(self):
        for lang in available_languages():
            with self.subTest(lang=lang):
                self.assertIsInstance(self._load(lang), dict)


if __name__ == "__main__":
    # Compact by default; pass -v for the per-test listing.
    unittest.main()

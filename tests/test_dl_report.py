#!/usr/bin/env python3
"""Cross-platform tests for tools/dl_report.py (per-item failure report).
Run: python -m unittest discover -s tests
"""
import os
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from dl_report import format_report, spot_failures, yt_failures  # noqa: E402

YT_LOG = """\
[youtube] Extracting URL
[download] Downloading item 1 of 3
[download] Destination: Song A.mp4
[download] Downloading item 2 of 3
ERROR: [youtube] vid2bcdef: Video unavailable
[download] Downloading item 3 of 3
ERROR: [youtube] vid3ghijk: Private video. Sign in if you've been granted access
"""

ID2TITLE = {"vid1abcde": "1. Song A", "vid2bcdef": "2. Song B", "vid3ghijk": "3. Song C"}


class TestYtFailures(unittest.TestCase):
    def test_pairs_id_to_title_with_verbatim_reason(self):
        out = yt_failures(YT_LOG, ID2TITLE)
        self.assertEqual(out, [
            ("2. Song B", "ERROR: [youtube] vid2bcdef: Video unavailable"),
            ("3. Song C",
             "ERROR: [youtube] vid3ghijk: Private video. Sign in if you've been granted access"),
        ])

    def test_no_errors_empty(self):
        self.assertEqual(yt_failures("[download] all good\n", ID2TITLE), [])

    def test_unknown_id_shows_bracketed_id(self):
        out = yt_failures("ERROR: [youtube] zzz999xxx: Deleted\n", ID2TITLE)
        self.assertEqual(out, [("[zzz999xxx]", "ERROR: [youtube] zzz999xxx: Deleted")])

    def test_error_without_extractor_id_uses_label(self):
        out = yt_failures("ERROR: unable to download video data: HTTP Error 403\n",
                          ID2TITLE, unknown_label="Unknown item")
        self.assertEqual(
            out, [("Unknown item", "ERROR: unable to download video data: HTTP Error 403")])


SPOT_LOG = """\
Downloaded "Artist - A"
Downloaded "Artist - C"
LookupError: No results found for: Artist - B
"""


class TestSpotFailures(unittest.TestCase):
    def test_only_undownloaded_with_matching_error(self):
        out = spot_failures(SPOT_LOG, ["Artist - A", "Artist - B", "Artist - C"])
        self.assertEqual(out, [("Artist - B", "LookupError: No results found for: Artist - B")])

    def test_label_when_no_matching_error(self):
        out = spot_failures('Downloaded "Artist - A"\n', ["Artist - A", "Artist - B"],
                            nodetail_label="no details")
        self.assertEqual(out, [("Artist - B", "no details")])

    def test_matches_on_title_part_only(self):
        # spotdl's error line names the track without the artist prefix.
        log = 'No results found for "Love Me Again"\n'
        out = spot_failures(log, ["John Newman - Love Me Again"], nodetail_label="?")
        self.assertEqual(out, [("John Newman - Love Me Again",
                                'No results found for "Love Me Again"')])

    def test_matches_undownloaded_despite_whitespace(self):
        log = 'Downloaded "Artist  -  A"\n'   # extra spaces vs the track string
        self.assertEqual(spot_failures(log, ["Artist - A"], nodetail_label="?"), [])

    def test_all_downloaded_empty(self):
        log = 'Downloaded "Artist - A"\nDownloaded "Artist - B"\n'
        self.assertEqual(spot_failures(log, ["Artist - A", "Artist - B"]), [])


class TestFormatReport(unittest.TestCase):
    def test_blocks_with_blank_line(self):
        out = format_report([("1. Song A", "Video unavailable"), ("2. Song B", "Private")])
        self.assertEqual(out, "1. Song A\n   Video unavailable\n\n2. Song B\n   Private")

    def test_empty(self):
        self.assertEqual(format_report([]), "")


if __name__ == "__main__":
    unittest.main()

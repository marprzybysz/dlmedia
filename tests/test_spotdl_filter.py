#!/usr/bin/env python3
"""Cross-platform tests for tools/spotdl_filter.py (Spotify pick/range selection).
Stdlib unittest only. Run: python -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from spotdl_filter import filter_file, parse_spec  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()

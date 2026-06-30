#!/usr/bin/env python3
"""Tests for tools/check_locales.py (locale completeness audit).
Run: python -m unittest discover -s tests
"""
import os
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from check_locales import audit  # noqa: E402


class TestAudit(unittest.TestCase):
    def test_complete_language(self):
        cats = {"en": {"a", "b"}, "pl": {"a", "b"}}
        self.assertEqual(audit(cats, "en")["pl"], {"missing": [], "extra": []})

    def test_missing_keys(self):
        cats = {"en": {"a", "b", "c"}, "es": {"a", "b"}}
        self.assertEqual(audit(cats, "en")["es"], {"missing": ["c"], "extra": []})

    def test_extra_keys(self):
        cats = {"en": {"a"}, "de": {"a", "x", "y"}}
        self.assertEqual(audit(cats, "en")["de"], {"missing": [], "extra": ["x", "y"]})

    def test_missing_is_sorted(self):
        cats = {"en": {"z", "a", "m"}, "fr": set()}
        self.assertEqual(audit(cats, "en")["fr"]["missing"], ["a", "m", "z"])

    def test_real_locales_complete(self):
        # The shipped locales must all be complete against en.
        import glob
        import json
        cats = {os.path.basename(f)[:-5]: set(json.load(open(f, encoding="utf-8")))
                for f in glob.glob(os.path.join(ROOT, "locales", "*.json"))}
        for lang, diff in audit(cats, "en").items():
            self.assertEqual(diff["missing"], [], f"{lang}.json missing keys")
            self.assertEqual(diff["extra"], [], f"{lang}.json has extra keys")


if __name__ == "__main__":
    unittest.main()

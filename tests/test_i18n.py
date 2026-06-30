#!/usr/bin/env python3
"""Cross-platform tests for gui/i18n.py + the shared locales/*.json catalog.
Stdlib unittest only. Run: python -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LOCALES = os.path.join(ROOT, "locales")
sys.path.insert(0, os.path.join(ROOT, "gui"))

from i18n import Catalog, available_languages  # noqa: E402


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
        self.assertEqual(Catalog("en").t("summary_spot", 3, 10), "Downloaded: 3 / 10")

    def test_template_wrong_arg_count_does_not_crash(self):
        # too few args -> return the template unformatted rather than raising
        self.assertIsInstance(Catalog("en").t("summary_spot", 3), str)

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
    unittest.main()

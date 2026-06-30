"""Locale catalog for the DLMedia GUI.

Reads the SAME locales/*.json files as the bash TUI/CLI — one source of truth for
all frontends. Qt-free so it's unit-testable. Adding a language = drop a new
locales/<lang>.json (no code change), which is the project's headline feature.
"""
from __future__ import annotations

import json
import os
import sys


def _locales_dir() -> str:
    # Explicit override wins (tests, custom installs).
    env = os.environ.get("DLMEDIA_LOCALES")
    if env:
        return env
    # PyInstaller bundle: locales are shipped inside the unpacked bundle dir.
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "locales")
    # Running from source: ../locales next to gui/.
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "locales"))


def available_languages() -> list[str]:
    d = _locales_dir()
    if not os.path.isdir(d):
        return ["en"]
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


class Catalog:
    """Holds the strings for one language. `t(key, *args)` returns the (formatted) string."""

    def __init__(self, lang: str = "en") -> None:
        self._data: dict[str, str] = {}
        self.lang = "en"
        self.load(lang)

    def load(self, lang: str) -> None:
        d = _locales_dir()
        path = os.path.join(d, f"{lang}.json")
        if not os.path.exists(path):
            path = os.path.join(d, "en.json")
            lang = "en"
        with open(path, encoding="utf-8") as f:
            self._data = json.load(f)
        self.lang = lang

    def t(self, key: str, *args) -> str:
        s = self._data.get(key, key)  # missing key -> show key (easy debug)
        if args:
            try:
                s = s % args
            except (TypeError, ValueError):
                pass
        return s

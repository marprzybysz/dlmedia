#!/usr/bin/env python3
"""Audit locales/*.json completeness — for adding new languages.

Compares every locale against a reference (default: en) and lists exactly which keys
each translation is missing or has extra, with a coverage count. The unit tests +
CI (tests/test_i18n.py) already FAIL on a mismatch; this is the friendly local tool
that tells a translator *what to fix*.

Run:  python3 tools/check_locales.py        (exit 1 if any locale is incomplete)
"""
from __future__ import annotations

import glob
import json
import os
import sys


def audit(catalogs: dict[str, set], ref: str = "en") -> dict[str, dict]:
    """catalogs: {lang: set(keys)}. Returns {lang: {'missing': [...], 'extra': [...]}} vs ref."""
    base = catalogs[ref]
    return {
        lang: {"missing": sorted(base - keys), "extra": sorted(keys - base)}
        for lang, keys in catalogs.items()
    }


def _load(locales_dir: str) -> dict[str, set]:
    cats = {}
    for f in sorted(glob.glob(os.path.join(locales_dir, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            cats[os.path.basename(f)[:-5]] = set(json.load(fh))
    return cats


def main() -> int:
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    cats = _load(os.path.join(root, "locales"))
    if "en" not in cats:
        print("no en.json reference found")
        return 1
    total = len(cats["en"])
    bad = False
    for lang, diff in sorted(audit(cats, "en").items()):
        miss, extra = diff["missing"], diff["extra"]
        have = total - len(miss)
        if not miss and not extra:
            print(f"{lang}.json   {have}/{total}  ✓ complete")
        else:
            bad = True
            print(f"{lang}.json   {have}/{total}  ✗")
            if miss:
                print(f"    missing ({len(miss)}): {', '.join(miss)}")
            if extra:
                print(f"    extra ({len(extra)}): {', '.join(extra)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

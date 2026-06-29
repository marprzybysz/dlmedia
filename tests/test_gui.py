#!/usr/bin/env python3
"""Tests for the GUI's Qt-free core (engine.py, i18n.py). No PySide6 needed.

Run directly (`python3 tests/test_gui.py`) or via `bash tests/run.sh`.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gui"))
from engine import build_command, is_spotify  # noqa: E402
from i18n import Catalog, available_languages  # noqa: E402

fails = 0


def check(name, cond):
    global fails
    print(("  ✓ " if cond else "  ✗ ") + name)
    if not cond:
        fails += 1


# ── engine: command construction (mirrors bash build_yt_args/cli_main) ──
cmd = build_command("https://youtu.be/x", "mp3", "192", "/tmp/o")
check("mp3 -> yt-dlp -x", cmd[0] == "yt-dlp" and "-x" in cmd)
check("mp3 quality 192K", "192K" in cmd)
check("mp3 output template", "/tmp/o/%(title)s.%(ext)s" in cmd)

cmd = build_command("https://youtu.be/x", "mp4", "best", "/tmp/o")
check("mp4 best selector", any("best[ext=mp4]" in a for a in cmd))
check("mp4 merges to mp4", "--merge-output-format" in cmd)

cmd = build_command("https://youtu.be/x", "mp4", "720", "/tmp/o")
check("mp4 720 caps height", any("height<=720" in a for a in cmd))

cmd = build_command("https://open.spotify.com/track/x", "mp4", "", "/tmp/o")
check("spotify -> spotdl", cmd[0] == "spotdl")
check("spotify default 320k", "320k" in cmd)
check("is_spotify true", is_spotify("https://open.spotify.com/x"))
check("is_spotify false", not is_spotify("https://youtu.be/x"))

try:
    build_command("https://youtu.be/x", "ogg")
    check("bad format raises", False)
except ValueError:
    check("bad format raises", True)

# ── i18n: shared locale catalog ──
en = Catalog("en")
pl = Catalog("pl")
zz = Catalog("zz")
check("en btn_download", en.t("btn_download") == "Download")
check("pl btn_download", pl.t("btn_download") == "Pobierz")
check("missing lang -> en", zz.t("btn_download") == "Download")
check("template formats", "%" not in en.t("preview_body", "a", "b", "c", "d", "e"))
check("missing key -> key", en.t("nope_xyz") == "nope_xyz")
check("gui key present", en.t("gui_done") == "Done")
check("languages include pl+en", {"pl", "en"}.issubset(set(available_languages())))

print(f"  ── gui core: {'all passed' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)

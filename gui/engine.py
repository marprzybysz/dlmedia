"""Download engine for the DLMedia GUI.

Builds the yt-dlp / spotdl command line. Deliberately Qt-free and side-effect-free
so it can be unit-tested, and so the GUI calls yt-dlp/spotdl directly (no bash) —
that's what lets the GUI run on native Windows. Mirrors the bash `build_yt_args`
/ `cli_main` logic so all frontends behave identically.
"""
from __future__ import annotations

import os
import shutil
import sys


def is_spotify(url: str) -> bool:
    return "open.spotify.com" in url or "spotify.link" in url


def _exe(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


def bundled_tools_dir() -> str:
    """Where bundled yt-dlp/ffmpeg/spotdl live: next to the frozen app (_internal/bin
    in a PyInstaller build) or gui/bin when running from source."""
    base = getattr(sys, "_MEIPASS", None)
    return os.path.join(base, "bin") if base else os.path.join(os.path.dirname(__file__), "bin")


def tool_path(name: str, tools_dir: str | None = None) -> str:
    """Full path to a bundled <name>(.exe) if present, else the bare name (PATH lookup).
    So a packaged build is self-contained, while running from source uses PATH."""
    d = bundled_tools_dir() if tools_dir is None else tools_dir
    p = os.path.join(d, _exe(name))
    return p if os.path.isfile(p) else name


def _ffmpeg_args(tools_dir: str | None = None) -> list[str]:
    """`--ffmpeg-location <dir>` when ffmpeg is bundled (so yt-dlp finds it off-PATH)."""
    d = bundled_tools_dir() if tools_dir is None else tools_dir
    return ["--ffmpeg-location", d] if os.path.isfile(os.path.join(d, _exe("ffmpeg"))) else []


def missing_deps(spotify: bool = False, which=shutil.which, tools_dir: str | None = None) -> list[str]:
    """External tools required but not available — neither bundled nor on PATH. Mirrors the
    bash check_deps: yt-dlp + ffmpeg always, spotdl only for Spotify. `which`/`tools_dir`
    are injectable so the check is unit-testable."""
    needed = ["yt-dlp", "ffmpeg"] + (["spotdl"] if spotify else [])
    return [t for t in needed
            if tool_path(t, tools_dir) == t and which(t) is None]


def build_command(url: str, fmt: str = "mp4", quality: str = "", out: str = ".",
                  tools_dir: str | None = None) -> list[str]:
    """Return the argv list to download `url`. `quality` empty = format default.
    Uses bundled yt-dlp/spotdl/ffmpeg when present (via tool_path), else PATH."""
    url = url.strip()
    if not url:
        raise ValueError("empty url")

    if is_spotify(url):
        q = quality or "320"
        return [tool_path("spotdl", tools_dir), "--bitrate", f"{q}k",
                "--output", f"{out}/{{artist}} - {{title}}", url]

    ytdlp = tool_path("yt-dlp", tools_dir)
    ff = _ffmpeg_args(tools_dir)

    if fmt == "mp3":
        q = quality or "320"
        return [ytdlp, "-x", "--audio-format", "mp3", "--audio-quality", f"{q}K",
                *ff, "-o", f"{out}/%(title)s.%(ext)s", url]

    if fmt == "mp4":
        q = quality or "best"
        # Codec-agnostic so 4K/8K (VP9/AV1) isn't capped to ~1080p H.264;
        # --merge-output-format mp4 remuxes the result into an .mp4 container.
        if q == "best":
            sel = "bestvideo+bestaudio/best"
        else:
            sel = f"bestvideo[height<={q}]+bestaudio/best[height<={q}]/best"
        return [ytdlp, "-f", sel, "--merge-output-format", "mp4",
                *ff, "-o", f"{out}/%(title)s.%(ext)s", url]

    raise ValueError(f"format must be mp3 or mp4, got {fmt!r}")

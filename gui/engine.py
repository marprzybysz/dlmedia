"""Download engine for the DLMedia GUI.

Builds the yt-dlp / spotdl command line. Deliberately Qt-free and side-effect-free
so it can be unit-tested, and so the GUI calls yt-dlp/spotdl directly (no bash) —
that's what lets the GUI run on native Windows. Mirrors the bash `build_yt_args`
/ `cli_main` logic so all frontends behave identically.
"""
from __future__ import annotations


def is_spotify(url: str) -> bool:
    return "open.spotify.com" in url or "spotify.link" in url


def build_command(url: str, fmt: str = "mp4", quality: str = "", out: str = ".") -> list[str]:
    """Return the argv list to download `url`. `quality` empty = format default."""
    url = url.strip()
    if not url:
        raise ValueError("empty url")

    if is_spotify(url):
        q = quality or "320"
        return ["spotdl", "--bitrate", f"{q}k",
                "--output", f"{out}/{{artist}} - {{title}}", url]

    if fmt == "mp3":
        q = quality or "320"
        return ["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", f"{q}K",
                "-o", f"{out}/%(title)s.%(ext)s", url]

    if fmt == "mp4":
        q = quality or "best"
        if q == "best":
            sel = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            sel = (f"bestvideo[height<={q}][ext=mp4]+bestaudio[ext=m4a]/"
                   f"best[height<={q}][ext=mp4]/best")
        return ["yt-dlp", "-f", sel, "--merge-output-format", "mp4",
                "-o", f"{out}/%(title)s.%(ext)s", url]

    raise ValueError(f"format must be mp3 or mp4, got {fmt!r}")

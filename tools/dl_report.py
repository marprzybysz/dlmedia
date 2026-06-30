#!/usr/bin/env python3
"""Build a per-item failure report from a yt-dlp / spotdl download log.

For the TUI summary's "Pokaż logi" screen: each failed item on one line, the error
that occurred below it, a blank line between entries. Pure/testable (fixtures); the
bash TUI calls the CLI. Log parsing is heuristic — it matches current yt-dlp/spotdl
output and may need revisiting if their format changes (see CLAUDE.md gotchas).

The reason shown is the VERBATIM error line (real diagnostic), never a translated
placeholder. yt-dlp pairs reliably: the video id appears in both the playlist listing
and the `ERROR: [extractor] <id>: <reason>` line, so we map id → title. spotdl is
best-effort (its errors don't always carry the track name): we match an error line on
the normalized full name or the title-part, else fall back to a caller-supplied label.

CLI:  dl_report.py <yt|spot> <log_file> <titles_file> <out_report_file>
        titles_file: yt → "<id>\\t<display title>" per line; spot → one track per line.
        writes the formatted report to out_report_file; prints the failure count to stdout.
        Localized fallback labels come from env: DLR_UNKNOWN (no-id header),
        DLR_NODETAIL (spotdl track with no matchable error line).
"""
from __future__ import annotations

import os
import re
import sys

_ERR = re.compile(r"^\s*ERROR:\s*", re.IGNORECASE)
_ID_IN_ERR = re.compile(r"^\s*ERROR:\s*\[[^\]]+\]\s*([\w-]{6,}):", re.IGNORECASE)


def yt_failures(log: str, id2title: dict[str, str],
                unknown_label: str = "?") -> list[tuple[str, str]]:
    """Each ERROR line -> (header, reason). Header = friendly title via id (else '[id]'
    or unknown_label); reason = the VERBATIM error line, so the log reads like a real
    diagnostic, not a translated placeholder."""
    out: list[tuple[str, str]] = []
    for line in log.splitlines():
        if not _ERR.match(line):
            continue
        m = _ID_IN_ERR.match(line)
        vid = m.group(1) if m else None
        header = id2title.get(vid) if vid else None
        if not header:
            header = f"[{vid}]" if vid else unknown_label
        out.append((header, line.strip()))
    return out


_SPOT_DOWNLOADED = re.compile(r'^\s*Downloaded\s+"(.+?)"', re.IGNORECASE)
# Real spotdl failure phrasings — not every one carries the words "error/failed".
_SPOT_ERR = re.compile(r"error|failed|lookuperror|no results|could not|unable",
                       re.IGNORECASE)


def _norm(s: str) -> str:
    """Lowercase + collapse whitespace, for tolerant track<->error-line matching."""
    return re.sub(r"\s+", " ", s).strip().lower()


def spot_failures(log: str, tracks: list[str],
                  nodetail_label: str = "?") -> list[tuple[str, str]]:
    """Best-effort: tracks not seen as Downloaded, paired with the VERBATIM spotdl error
    line that mentions them. No match -> nodetail_label (honest, not tautological)."""
    downloaded = set()
    for line in log.splitlines():
        m = _SPOT_DOWNLOADED.match(line)
        if m:
            downloaded.add(_norm(m.group(1)))
    err_lines = [ln.strip() for ln in log.splitlines()
                 if _SPOT_ERR.search(ln) and "skipping" not in ln.lower()]
    out: list[tuple[str, str]] = []
    for t in tracks:
        name = t.strip()
        if _norm(name) in downloaded:
            continue
        key = _norm(name)
        title = key.split(" - ", 1)[-1]   # "artist - title" -> "title"
        reason = next(
            (e for e in err_lines if key in _norm(e) or (title and title in _norm(e))),
            nodetail_label,
        )
        out.append((name, reason))
    return out


def format_report(failures: list[tuple[str, str]]) -> str:
    """'header\\n  reason' blocks, one blank line apart."""
    return "\n\n".join(f"{header}\n   {reason}" for header, reason in failures)


def _read_titles(path: str, tool: str):
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    if tool == "yt":
        d = {}
        for ln in lines:
            vid, _, title = ln.partition("\t")
            if vid:
                d[vid] = title or vid
        return d
    return lines


if __name__ == "__main__":
    tool, log_file, titles_file, out_file = sys.argv[1:5]
    with open(log_file, encoding="utf-8", errors="replace") as f:
        log = f.read()
    titles = _read_titles(titles_file, tool)
    unknown = os.environ.get("DLR_UNKNOWN", "?")
    nodetail = os.environ.get("DLR_NODETAIL", "?")
    failures = (yt_failures(log, titles, unknown) if tool == "yt"
                else spot_failures(log, titles, nodetail))
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(format_report(failures) + ("\n" if failures else ""))
    print(len(failures))

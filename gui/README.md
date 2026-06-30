# DLMedia GUI (PySide6)

The cross-platform (Windows-first) graphical frontend — for people who'd rather not
touch a terminal. It's a **separate app from the bash TUI**: it calls `yt-dlp`/`spotdl`
directly (no bash, no `dialog`), so it runs natively on Windows. It reads the **same
`../locales/*.json`** catalog as the TUI/CLI, so every frontend speaks every language.

> Status: **working skeleton** — URL → format/quality/folder → download with live log.
> UX is intentionally minimal and meant to grow (queue, history, drag-and-drop, etc.).

## Run from source

```bash
pip install -r gui/requirements.txt      # PySide6
# plus yt-dlp (and spotdl for Spotify) on PATH
python3 gui/dlmedia_gui.py
```

Start in a given language: `DLMEDIA_LANG=pl python3 gui/dlmedia_gui.py`
(the picker in the top-right switches at runtime). Languages are discovered from
`../locales/*.json`; add one by dropping a new file there.

## Layout

| File | Role |
|---|---|
| `dlmedia_gui.py` | Qt window + wiring (the only file that imports PySide6) |
| `engine.py` | builds the yt-dlp/spotdl command line — Qt-free, unit-tested |
| `i18n.py` | loads `locales/*.json` into a `Catalog` — Qt-free, unit-tested |

`engine.py` mirrors the bash `build_yt_args`/`cli_main` logic so the GUI behaves
identically to the CLI/TUI. Tests: `python3 tests/test_gui.py` (also run by `bash tests/run.sh`).

## Packaging (later)

Planned: PyInstaller → single `.exe`, NSIS installer, bundle `yt-dlp.exe`/`ffmpeg`,
ship `locales/` next to the exe (set `DLMEDIA_LOCALES`), and a GitHub-Releases update check.

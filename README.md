# dlmedia

A simple terminal UI (TUI) for downloading media from **YouTube**, **Spotify** and **SoundCloud**, built for WSL/Linux. Wraps [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) and [`spotdl`](https://github.com/spotDL/spotify-downloader) behind a `dialog` interface — no flags to memorize, just paste a URL.

> UI is bilingual: **Polish** (default) and **English**, chosen on first run.

## Features

- **Playlists, `menuconfig`-style** — one checklist with **every item pre-selected**; OK downloads the lot, or uncheck the ones you don't want (Space toggles, like the Linux kernel's `make menuconfig`). Works for YouTube playlists and Spotify albums/playlists alike.
- **YouTube** — single videos and playlists
- **Spotify** — albums and playlists (via `spotdl`)
- **SoundCloud** — tracks and sets/playlists (via `yt-dlp`; audio, so pick MP3). Anything else `yt-dlp` supports tends to work too, since unrecognized URLs fall through to it.
- **Format & quality** — MP4 video up to **8K** (best/4320/2160 (4K)/1440/1080/720/480/360) or MP3 audio (320/192/128 kbps). The selector is codec-agnostic (VP9/AV1) so high-res isn't capped at 1080p, then remuxed to `.mp4`.
- **Info preview** before download (title, duration, approximate size)
- **Skip or overwrite** files already downloaded (per playlist/album subfolder)
- **Live download output** streamed inside the TUI, plus a summary with error reporting
- **Setup wizard** on first run; settings saved to `dlmedia.conf`
- **Bilingual UI** (PL/EN), selectable in the wizard

## Requirements

| Requirement | Notes |
|---|---|
| **bash ≥ 4.0** | Uses associative arrays and `mapfile`. Checked at startup. |
| **dialog** | The TUI itself. |
| **yt-dlp** | YouTube downloads. |
| **ffmpeg** | Audio extraction / muxing. |
| **python3** | Parses Spotify track metadata. |
| **GNU coreutils** | Provides `stdbuf` (required) and `numfmt` (optional). |
| **spotdl** *(optional)* | Only needed for Spotify URLs. `pipx install spotdl` |

### Install dependencies

**Debian / Ubuntu / WSL:**
```bash
sudo apt update
sudo apt install dialog ffmpeg python3 python3-pip
python3 -m pip install -U yt-dlp
pipx install spotdl          # optional, for Spotify
```

**Arch:**
```bash
sudo pacman -S dialog ffmpeg python yt-dlp
pipx install spotdl          # optional
```

## Supported systems

| System | Status |
|---|---|
| **Linux** (any modern distro) | ✅ Fully supported |
| **Windows via WSL** | ✅ Primary target |
| **macOS** | ⚠️ Needs newer bash + GNU coreutils: `brew install bash dialog coreutils ffmpeg yt-dlp` — and the script must be run with Homebrew's bash, since macOS ships bash 3.2. |
| **Native Windows** (no WSL) | ❌ Not supported (no bash/`dialog`) |
| **\*BSD** | ❌ `stdbuf` (GNU coreutils) is not available |

The default download path is `/mnt/c/Users/<you>/Downloads/yt-dlp` (a WSL → Windows location); change it in the setup wizard on non-WSL systems.

## Install

```bash
git clone https://github.com/marprzybysz/dlmedia.git
cd dlmedia
chmod +x dlmedia
./dlmedia
```

On first run a setup wizard asks for your language, default format/quality, download folder, and whether to create per-playlist subfolders. It writes `dlmedia.conf` next to the script (this file is git-ignored — it's personal).

### Desktop entry (Linux)

To get a **DLMedia** icon in your GNOME/KDE/etc. application menu (launches the TUI in a terminal):

```bash
./install-desktop.sh              # install icon + menu entry (no root, ~/.local/share)
./install-desktop.sh --uninstall  # remove it
```

This installs `dlmedia.desktop` and the SVG icon from `assets/` for the current user only.

## Usage

```bash
./dlmedia              # interactive TUI (default)
./dlmedia --setup      # re-run the configuration wizard
./dlmedia --update     # update yt-dlp
./dlmedia --help       # show usage
```

Inside the TUI: paste a YouTube or Spotify URL, follow the prompts, and after the download a summary appears with **Back** (download something else) or **Exit**.

### Non-interactive CLI

For scripts, automation, or when you just want one download without the TUI:

```bash
./dlmedia --url <URL> [--format mp3|mp4] [--quality <Q>] [--out <DIR>] [--lang pl|en]

# examples
./dlmedia --url 'https://youtu.be/...' --format mp3 --quality 320
./dlmedia --url 'https://open.spotify.com/album/...' --out ~/Music
```

CLI mode needs **neither `dialog` nor `stdbuf`**, so it runs where the TUI can't — including **Git Bash on native Windows** (no WSL needed). Output streams to the terminal; the exit code reflects success/failure. Defaults fall back to your `dlmedia.conf` (or `mp4`/`best` and `mp3`/`320` if unset).

## Tests

```bash
bash tests/run.sh
```

Covers the non-interactive logic — `build_yt_args`, `cli_main` argument parsing & routing (with stubbed yt-dlp/spotdl), `load_lang` + fallback, and locale key parity. The `dialog` TUI screens can't be tested non-interactively (each blocks on input), so they're out of scope. The suite loads the script's functions via `DLMEDIA_LIB=1 source ./dlmedia` (a hook that defines functions without running the app).

## Configuration

`dlmedia.conf` is generated by the setup wizard. You can also edit it by hand:

| Key | Values | Meaning |
|---|---|---|
| `UI_LANG` | `pl` \| `en` | UI language (defaults to `pl` if absent) |
| `DOWNLOAD_DIR` | path | Where files are saved |
| `DEFAULT_FORMAT` | `mp4` \| `mp3` | Default download format |
| `DEFAULT_QUALITY` | bitrate / resolution | e.g. `best`, `1080`, `320` |
| `ASK_FORMAT` | `true` \| `false` | Prompt for format each time |
| `ASK_QUALITY` | `true` \| `false` | Prompt for quality each time |
| `PLAYLIST_SUBFOLDERS` | `true` \| `false` | Create a subfolder per playlist/album |

## Translations

The UI is multilingual — Polish and English ship today, and **adding a language is just one JSON file** (no code changes). To add, say, Spanish:

```bash
cp locales/en.json locales/es.json     # then translate the values (keep the keys!)
python3 tools/check_locales.py         # lists any missing/extra keys per language
```

`check_locales.py` reports each locale's coverage against English (e.g. `es.json 78/80 ✗ missing: btn_exit, logs_title`). The test suite enforces the same parity in CI, so an incomplete translation fails the build. The app auto-detects every `locales/*.json` and offers it in the setup wizard's language menu. PRs with new languages welcome. 🌍

## Roadmap

- ✅ Non-interactive CLI mode (`--url … --format mp3 --quality 320`).
- Linux desktop integration (`.desktop` entry + icon for GNOME/KDE).
- Windows GUI (separate PySide6 app sharing the same `locales/` catalog and download engine).
- More UI languages — adding one is just a new `locales/<lang>.json`; translations welcome.

## Disclaimer

dlmedia is a personal/educational front-end that orchestrates [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) and [`spotdl`](https://github.com/spotDL/spotify-downloader); it hosts and distributes no media. **Download only content you have the right to** — material you own, that is in the public domain, or that the rights holder permits. You are responsible for complying with the Terms of Service of the source platforms and with the copyright law of your country. The author provides this software "as is", without warranty, and accepts no liability for how it is used. Not affiliated with, endorsed by, or connected to YouTube, Spotify, or SoundCloud.

## License

[GPL-3.0](LICENSE) — free software; you can redistribute and modify it under the terms of the GNU General Public License v3. "DLMedia" the name/brand is the author's.

## Author

Marcin Przybysz ([@marprzybysz](https://github.com/marprzybysz))

Bug reports and suggestions welcome via [GitHub issues](https://github.com/marprzybysz/dlmedia/issues).

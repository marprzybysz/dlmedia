# Building the DLMedia GUI (Windows .exe + installer)

## Run from source (any OS, incl. WSL2/WSLg)

```bash
pip install -r gui/requirements.txt          # PySide6
python3 gui/dlmedia_gui.py                    # window opens (WSLg shows it under WSL2)
```
On WSL2 the GUI runs fine through **WSLg** — handy for developing/seeing the UI. But see the
caveat below: WSL2 can run it, it **cannot build the Windows `.exe`**.

## Build the Windows `.exe` — must run on **native Windows**

⚠️ **PyInstaller is not a cross-compiler.** Running it under **WSL2 (Linux) produces a Linux
binary, not a `.exe`.** To get a Windows executable you need real Windows: your Windows host,
a Windows VM, or a `windows-latest` GitHub Actions runner. (Wine is unreliable for PySide6 —
not recommended.)

On Windows (PowerShell / cmd), from the repo root:

```powershell
py -m pip install pyinstaller PySide6
py -m PyInstaller gui\dlmedia.spec
```
→ produces `dist\DLMedia\DLMedia.exe` (one-folder build).

### Yes, there will be DLLs — that's normal 🙂
A PySide6 build bundles a pile of DLLs next to the `.exe`: the **Qt6** libraries
(`Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`), the **Python** runtime (`python3xx.dll`),
the **MSVC runtime**, and Qt **platform plugins** (`platforms\qwindows.dll`). That's why the
folder is ~40–80 MB. They must ship together with the exe — the NSIS installer packs the
whole `dist\DLMedia\` folder, so the user never sees them.

### App icon (optional)
Convert `assets/dlmedia.svg` → `assets/dlmedia.ico` (e.g. ImageMagick:
`magick assets/dlmedia.svg -define icon:auto-resize=256,64,48,32,16 assets/dlmedia.ico`).
The spec picks it up automatically if present.

### Bundling yt-dlp / ffmpeg (recommended — self-contained app)
So the user installs and clicks with **nothing else to set up**, ship the tools inside the app.
On Windows, before building:
```powershell
.\gui\fetch-tools.ps1
```
This downloads `yt-dlp.exe` + `ffmpeg.exe`/`ffprobe.exe` into `gui/bin/` (git-ignored). The spec
auto-bundles `gui/bin/` into `_internal/bin`, and the app uses them automatically
(`engine.tool_path`, `--ffmpeg-location`). If `gui/bin/` is empty, the app falls back to PATH and
just **warns** when a tool is missing (`missing_deps`).

**Spotify:** `spotdl` is a Python package (no single `.exe`), so it isn't auto-bundled — for
Spotify support, `pipx install spotdl` on the target (the app finds it on PATH). YouTube/SoundCloud
work fully from the bundle.

## Make the installer (on Windows)

Install [NSIS](https://nsis.sourceforge.io/) (or `choco install nsis`), then **from the repo
root** (the script's `File`/`OutFile` paths are root-relative):
```powershell
makensis gui\installer.nsi            # or: makensis /DMyAppVersion=1.2.3 gui\installer.nsi
```
→ produces `gui\Output\DLMedia-Setup-<version>.exe` (bilingual PL/EN installer; version defaults
to `0.1.0` when `/DMyAppVersion` is omitted). CI fills the version from the release tag.

**SmartScreen note:** unsigned installers trigger “Windows protected your PC — unknown
publisher”. It still installs (More info → Run anyway). A code-signing certificate removes the
warning; not worth it at the alpha stage.

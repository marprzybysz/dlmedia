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
folder is ~40–80 MB. They must ship together with the exe — the Inno Setup script packs the
whole `dist\DLMedia\` folder, so the user never sees them.

### App icon (optional)
Convert `assets/dlmedia.svg` → `assets/dlmedia.ico` (e.g. ImageMagick:
`magick assets/dlmedia.svg -define icon:auto-resize=256,64,48,32,16 assets/dlmedia.ico`).
The spec picks it up automatically if present.

### Bundling yt-dlp / ffmpeg (optional)
By default the app finds `yt-dlp`/`ffmpeg` on PATH and warns if missing (`missing_deps`).
To ship them inside the app, drop `yt-dlp.exe` / `ffmpeg.exe` in `gui/bin/` and uncomment the
`binaries` lines in `gui/dlmedia.spec`.

## Make the installer (on Windows)

Install [Inno Setup](https://jrsoftware.org/isdl.php), then:
```powershell
iscc gui\installer.iss
```
→ produces `Output\DLMedia-Setup-0.1.0.exe` (bilingual PL/EN installer).

**SmartScreen note:** unsigned installers trigger “Windows protected your PC — unknown
publisher”. It still installs (More info → Run anyway). A code-signing certificate removes the
warning; not worth it at the alpha stage.

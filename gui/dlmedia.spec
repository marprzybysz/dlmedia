# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the DLMedia GUI. Build on Windows (see gui/BUILD.md):
#   pip install pyinstaller PySide6
#   pyinstaller gui/dlmedia.spec
# Produces dist/DLMedia/DLMedia.exe (one-folder build), bundling the locale catalog.
#
# To make the app fully self-contained (no deps on the user's PATH), put yt-dlp.exe,
# ffmpeg.exe (+ ffprobe.exe) and optionally spotdl.exe in gui/bin/ before building —
# run gui/fetch-tools.ps1 to download them. They get bundled into _internal/bin and the
# app uses them automatically (see engine.tool_path). If gui/bin/ is empty, the app falls
# back to PATH and warns (missing_deps) when a tool is absent.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
GUI = os.path.join(ROOT, "gui")
BIN = os.path.join(GUI, "bin")
_icon = os.path.join(ROOT, "assets", "dlmedia.ico")  # generate from assets/dlmedia.svg

_datas = [(os.path.join(ROOT, "locales"), "locales")]   # → bundle/locales (see i18n._locales_dir)
if os.path.isdir(BIN) and os.listdir(BIN):
    _datas.append((BIN, "bin"))                          # → bundle/bin (see engine.bundled_tools_dir)

a = Analysis(
    [os.path.join(GUI, "dlmedia_gui.py")],
    pathex=[GUI],                       # so `import engine` / `import i18n` resolve
    binaries=[],
    datas=_datas,
    hiddenimports=["engine", "i18n"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DLMedia",
    console=False,                      # GUI app, no console window
    icon=_icon if os.path.exists(_icon) else None,
)

coll = COLLECT(exe, a.binaries, a.datas, name="DLMedia")

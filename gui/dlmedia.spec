# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the DLMedia GUI. Build on Windows (see gui/BUILD.md):
#   pip install pyinstaller PySide6
#   pyinstaller gui/dlmedia.spec
# Produces dist/DLMedia/DLMedia.exe (one-folder build), bundling the locale catalog.
#
# yt-dlp.exe / ffmpeg.exe are NOT bundled by default — the app finds them on PATH and
# warns (missing_deps) if absent. To ship them inside the app, drop the .exe files in
# gui/bin/ and uncomment the `binaries` entries below.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
GUI = os.path.join(ROOT, "gui")
_icon = os.path.join(ROOT, "assets", "dlmedia.ico")  # generate from assets/dlmedia.svg

a = Analysis(
    [os.path.join(GUI, "dlmedia_gui.py")],
    pathex=[GUI],                       # so `import engine` / `import i18n` resolve
    binaries=[
        # (os.path.join(GUI, "bin", "yt-dlp.exe"), "."),
        # (os.path.join(GUI, "bin", "ffmpeg.exe"), "."),
    ],
    datas=[(os.path.join(ROOT, "locales"), "locales")],   # → bundle/locales (see i18n._locales_dir)
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

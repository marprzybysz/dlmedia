#!/usr/bin/env python3
"""DLMedia — GUI frontend (PySide6).

A bash-free, Windows-first GUI over yt-dlp/spotdl that shares the project's
locales/*.json catalog with the TUI/CLI. Two views behind a small top navbar:

  • Download — paste URL → Enter → pick format/quality → live verbose log + a
    progress bar parsed from yt-dlp's output. Mirrors the bash TUI's flow.
  • Settings — language switch, app version, repo link, license.

Minimal and simple by design; the only file that imports Qt.
"""
from __future__ import annotations

import os
import re
import sys

try:
    from PySide6.QtCore import QProcess, Qt
    from PySide6.QtWidgets import (
        QApplication, QButtonGroup, QComboBox, QFileDialog, QFrame, QHBoxLayout,
        QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
        QPushButton, QStackedWidget, QVBoxLayout, QWidget,
    )
except ImportError:
    sys.exit("PySide6 is required: pip install -r gui/requirements.txt")

sys.path.insert(0, os.path.dirname(__file__))
from engine import build_command, is_spotify, missing_deps  # noqa: E402
from i18n import Catalog, available_languages  # noqa: E402

APP_VERSION = os.environ.get("DLMEDIA_VERSION", "0.1.0-dev")
REPO_URL = "https://github.com/marprzybysz/dlmedia"

QUALITY = {
    "mp4": ["best", "4320", "2160", "1440", "1080", "720", "480", "360"],
    "mp3": ["320", "192", "128"],
}

# Pull the download percentage out of yt-dlp's "[download]  62.0% of …" lines.
_PCT = re.compile(r"\[download\]\s+([0-9]{1,3}(?:\.[0-9]+)?)%")

STYLE = """
QWidget { font-size: 13px; color: #20242c; }
#Page { background: #f6f7f9; }
#Title { font-size: 20px; font-weight: bold; color: #161a22; }
#Subtitle { color: #8a909a; }
#Nav { background: #ffffff; border-bottom: 1px solid #e4e7ec; }
QPushButton#NavBtn {
    border: none; background: transparent; padding: 10px 16px;
    color: #5b616b; font-weight: 600;
}
QPushButton#NavBtn:hover { color: #2563eb; }
QPushButton#NavBtn:checked { color: #2563eb; border-bottom: 2px solid #2563eb; }
QLineEdit, QComboBox {
    border: 1px solid #cfd4dc; border-radius: 6px; padding: 6px 8px; background: #fff;
}
QLineEdit:focus, QComboBox:focus { border-color: #2563eb; }
QPushButton#Primary {
    background: #2563eb; color: #fff; border: none; border-radius: 6px;
    padding: 9px 16px; font-weight: 600;
}
QPushButton#Primary:hover { background: #1d4ed8; }
QPushButton#Primary:disabled { background: #a9c0f2; }
QPushButton { border: 1px solid #cfd4dc; border-radius: 6px; padding: 7px 12px; background: #fff; }
QPushButton:hover { border-color: #2563eb; }
#Log {
    background: #1e2030; color: #d6deeb; border: none; border-radius: 6px;
    font-family: Consolas, "Courier New", monospace; font-size: 12px;
}
QProgressBar { border: none; border-radius: 5px; background: #e4e7ec; height: 10px; }
QProgressBar::chunk { background: #2563eb; border-radius: 5px; }
#Status { color: #5b616b; font-weight: 600; }
#RepoLink, #RepoLink a { color: #2563eb; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cat = Catalog(os.environ.get("DLMEDIA_LANG", "en"))
        self.proc: QProcess | None = None
        self._build_ui()
        self.retranslate()

    # ── layout ────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top navbar: title + Download / Settings view switches.
        nav = QWidget(objectName="Nav")
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(14, 6, 14, 0)
        nl.setSpacing(4)
        self.title = QLabel("DLMedia", objectName="Title")
        nl.addWidget(self.title)
        nl.addSpacing(20)
        self.nav_dl = QPushButton(objectName="NavBtn", checkable=True, checked=True)
        self.nav_set = QPushButton(objectName="NavBtn", checkable=True)
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.nav_dl)
        grp.addButton(self.nav_set)
        self.nav_dl.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.nav_set.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        nl.addWidget(self.nav_dl)
        nl.addWidget(self.nav_set)
        nl.addStretch()
        outer.addWidget(nav)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._download_page())
        self.stack.addWidget(self._settings_page())
        outer.addWidget(self.stack, 1)

        self.setCentralWidget(central)
        self.setWindowTitle("DLMedia")
        self.setStyleSheet(STYLE)
        self.resize(660, 560)

    def _download_page(self) -> QWidget:
        page = QWidget(objectName="Page")
        L = QVBoxLayout(page)
        L.setContentsMargins(18, 14, 18, 16)
        L.setSpacing(9)

        self.subtitle = QLabel(objectName="Subtitle")
        L.addWidget(self.subtitle)

        self.url_label = QLabel()
        L.addWidget(self.url_label)
        self.url_edit = QLineEdit()
        self.url_edit.returnPressed.connect(self._download)   # Enter = download
        L.addWidget(self.url_edit)

        fq = QHBoxLayout()
        self.format_label = QLabel()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "mp4"])
        self.format_combo.currentTextChanged.connect(self._refresh_quality)
        self.quality_label = QLabel()
        self.quality_combo = QComboBox()
        fq.addWidget(self.format_label)
        fq.addWidget(self.format_combo)
        fq.addSpacing(16)
        fq.addWidget(self.quality_label)
        fq.addWidget(self.quality_combo)
        fq.addStretch()
        L.addLayout(fq)

        out = QHBoxLayout()
        self.out_label = QLabel()
        self.out_edit = QLineEdit(os.path.expanduser("~"))
        self.browse_btn = QPushButton()
        self.browse_btn.clicked.connect(self._browse)
        out.addWidget(self.out_label)
        out.addWidget(self.out_edit, 1)
        out.addWidget(self.browse_btn)
        L.addLayout(out)

        self.download_btn = QPushButton(objectName="Primary")
        self.download_btn.clicked.connect(self._download)
        L.addWidget(self.download_btn)

        ps = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.status = QLabel(objectName="Status")
        ps.addWidget(self.progress, 1)
        ps.addWidget(self.status)
        L.addLayout(ps)

        self.log = QPlainTextEdit(objectName="Log")
        self.log.setReadOnly(True)
        L.addWidget(self.log, 1)

        self._refresh_quality(self.format_combo.currentText())
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget(objectName="Page")
        L = QVBoxLayout(page)
        L.setContentsMargins(18, 16, 18, 16)
        L.setSpacing(11)

        lang = QHBoxLayout()
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(available_languages())
        self.lang_combo.setCurrentText(self.cat.lang)
        self.lang_combo.currentTextChanged.connect(self._change_lang)
        lang.addWidget(self.lang_label)
        lang.addWidget(self.lang_combo)
        lang.addStretch()
        L.addLayout(lang)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e4e7ec;")
        L.addWidget(sep)

        about = QLabel("DLMedia", objectName="Title")
        L.addWidget(about)
        self.version_lbl = QLabel()
        self.author_lbl = QLabel()
        self.repo_lbl = QLabel(objectName="RepoLink")
        self.repo_lbl.setTextFormat(Qt.RichText)
        self.repo_lbl.setOpenExternalLinks(True)
        self.license_lbl = QLabel()
        for w in (self.version_lbl, self.author_lbl, self.repo_lbl, self.license_lbl):
            L.addWidget(w)
        L.addStretch()
        return page

    # ── i18n ──────────────────────────────────────────────────────────────
    def retranslate(self) -> None:
        t = self.cat.t
        self.nav_dl.setText("⬇  " + t("btn_download"))
        self.nav_set.setText("⚙  " + t("gui_settings"))
        self.subtitle.setText(t("gui_subtitle"))
        self.url_label.setText(t("url_prompt"))
        self.format_label.setText(t("format_q"))
        self.quality_label.setText(t("gui_quality"))
        self.out_label.setText(t("gui_out_label"))
        self.browse_btn.setText(t("gui_browse"))
        self.download_btn.setText(t("btn_download"))
        if not (self.proc and self.proc.state() != QProcess.NotRunning):
            self.status.setText(t("gui_ready"))
        # Settings.
        self.lang_label.setText(t("gui_lang_label"))
        self.version_lbl.setText(f'{t("gui_version")}: {APP_VERSION}')
        self.author_lbl.setText(f'{t("gui_author")}: Marcin Przybysz')
        self.repo_lbl.setText(f'{t("gui_repo")}: <a href="{REPO_URL}">{REPO_URL}</a>')
        self.license_lbl.setText(f'{t("gui_license")}: GPL-3.0')

    def _change_lang(self, lang: str) -> None:
        self.cat.load(lang)
        self.retranslate()

    # ── helpers ─────────────────────────────────────────────────────────────
    def _refresh_quality(self, fmt: str) -> None:
        self.quality_combo.clear()
        self.quality_combo.addItems(QUALITY.get(fmt, []))

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, self.cat.t("gui_out_label"), self.out_edit.text())
        if d:
            self.out_edit.setText(d)

    # ── download ────────────────────────────────────────────────────────────
    def _download(self) -> None:
        if self.proc and self.proc.state() != QProcess.NotRunning:
            return  # a download is already running
        url = self.url_edit.text().strip()
        if not url:
            self.status.setText(self.cat.t("err_no_url"))
            return
        miss = missing_deps(is_spotify(url))
        if miss:
            QMessageBox.warning(
                self, self.cat.t("deps_title"),
                "  ✗  " + "\n  ✗  ".join(miss) + "\n\n" + self.cat.t("deps_footer"),
            )
            self.status.setText(self.cat.t("deps_title"))
            return
        fmt = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        out = self.out_edit.text() or "."
        os.makedirs(out, exist_ok=True)
        argv = build_command(url, fmt, quality, out)

        self.log.clear()
        self.log.appendPlainText("$ " + " ".join(argv) + "\n")
        self.progress.setValue(0)
        self.download_btn.setEnabled(False)
        self.status.setText(self.cat.t("downloading") + "…")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._finished)
        self.proc.errorOccurred.connect(self._error)
        self.proc.start(argv[0], argv[1:])

    def _read(self) -> None:
        if not self.proc:
            return
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        self.log.appendPlainText(data.rstrip("\n"))
        m = None
        for m in _PCT.finditer(data):
            pass
        if m:
            self.progress.setValue(round(float(m.group(1))))

    def _finished(self, code: int, _status) -> None:
        self.download_btn.setEnabled(True)
        if code == 0:
            self.progress.setValue(100)
            self.status.setText(self.cat.t("gui_done"))
        else:
            self.status.setText(self.cat.t("gui_error"))

    def _error(self, _err) -> None:
        self.download_btn.setEnabled(True)
        self.status.setText(self.cat.t("gui_error"))


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

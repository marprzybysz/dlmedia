#!/usr/bin/env python3
"""DLMedia — GUI frontend (PySide6).

A bash-free, cross-platform (Windows-first) GUI over yt-dlp/spotdl that shares the
project's locales/*.json catalog with the TUI/CLI. This is a working skeleton:
URL in → pick format/quality/folder → download with live output. UX is intentionally
minimal and meant to be grown.
"""
from __future__ import annotations

import os
import sys

try:
    from PySide6.QtCore import QProcess, Qt
    from PySide6.QtWidgets import (
        QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
        QMainWindow, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
    )
except ImportError:
    sys.exit("PySide6 is required: pip install -r gui/requirements.txt")

sys.path.insert(0, os.path.dirname(__file__))
from engine import build_command, is_spotify  # noqa: E402
from i18n import Catalog, available_languages  # noqa: E402

QUALITY = {
    "mp4": ["best", "4320", "2160", "1440", "1080", "720", "480", "360"],
    "mp3": ["320", "192", "128"],
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cat = Catalog(os.environ.get("DLMEDIA_LANG", "en"))
        self.proc: QProcess | None = None
        self._build_ui()
        self.retranslate()

    def _build_ui(self) -> None:
        root = QVBoxLayout()

        # Header: title + language picker.
        top = QHBoxLayout()
        self.title = QLabel("DLMedia")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("color: gray;")
        top.addWidget(self.title)
        top.addWidget(self.subtitle)
        top.addStretch()
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(available_languages())
        self.lang_combo.setCurrentText(self.cat.lang)
        self.lang_combo.currentTextChanged.connect(self._change_lang)
        top.addWidget(self.lang_label)
        top.addWidget(self.lang_combo)
        root.addLayout(top)

        # URL.
        self.url_label = QLabel()
        self.url_edit = QLineEdit()
        root.addWidget(self.url_label)
        root.addWidget(self.url_edit)

        # Format + quality.
        fq = QHBoxLayout()
        self.format_label = QLabel()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3"])
        self.format_combo.currentTextChanged.connect(self._refresh_quality)
        self.quality_label = QLabel()
        self.quality_combo = QComboBox()
        fq.addWidget(self.format_label)
        fq.addWidget(self.format_combo)
        fq.addSpacing(16)
        fq.addWidget(self.quality_label)
        fq.addWidget(self.quality_combo)
        fq.addStretch()
        root.addLayout(fq)

        # Output folder.
        out = QHBoxLayout()
        self.out_label = QLabel()
        self.out_edit = QLineEdit(os.path.expanduser("~"))
        self.browse_btn = QPushButton()
        self.browse_btn.clicked.connect(self._browse)
        out.addWidget(self.out_label)
        out.addWidget(self.out_edit)
        out.addWidget(self.browse_btn)
        root.addLayout(out)

        # Download button + status.
        self.download_btn = QPushButton()
        self.download_btn.clicked.connect(self._download)
        root.addWidget(self.download_btn)
        self.status = QLabel()
        root.addWidget(self.status)

        # Live log.
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        root.addWidget(self.log, stretch=1)

        self._refresh_quality(self.format_combo.currentText())
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(640, 540)

    # ── i18n ──────────────────────────────────────────────────────────────
    def retranslate(self) -> None:
        t = self.cat.t
        self.setWindowTitle("DLMedia")
        self.subtitle.setText(t("gui_subtitle"))
        self.lang_label.setText(t("gui_lang_label"))
        self.url_label.setText(t("url_prompt"))
        self.format_label.setText(t("format_q"))
        self.quality_label.setText(t("gui_quality"))
        self.out_label.setText(t("gui_out_label"))
        self.browse_btn.setText(t("gui_browse"))
        self.download_btn.setText(t("btn_download"))
        self.status.setText(t("gui_ready"))

    def _change_lang(self, lang: str) -> None:
        self.cat.load(lang)
        self.retranslate()

    def _refresh_quality(self, fmt: str) -> None:
        self.quality_combo.clear()
        self.quality_combo.addItems(QUALITY.get(fmt, []))

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, self.cat.t("gui_out_label"), self.out_edit.text())
        if d:
            self.out_edit.setText(d)

    # ── download ──────────────────────────────────────────────────────────
    def _download(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            self.status.setText(self.cat.t("err_no_url"))
            return
        fmt = self.format_combo.currentText()
        # spotify ignores the mp4/mp3 toggle (audio only)
        quality = self.quality_combo.currentText()
        out = self.out_edit.text() or "."
        os.makedirs(out, exist_ok=True)
        argv = build_command(url, fmt, quality, out)

        self.log.clear()
        self.log.appendPlainText("$ " + " ".join(argv) + "\n")
        self.download_btn.setEnabled(False)
        self.status.setText(self.cat.t("downloading") + "…")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._finished)
        self.proc.errorOccurred.connect(self._error)
        self.proc.start(argv[0], argv[1:])

    def _read(self) -> None:
        if self.proc:
            data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
            self.log.appendPlainText(data.rstrip("\n"))

    def _finished(self, code: int, _status) -> None:
        self.download_btn.setEnabled(True)
        self.status.setText(self.cat.t("gui_done") if code == 0 else self.cat.t("gui_error"))

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

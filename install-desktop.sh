#!/usr/bin/env bash
# Install (or remove) the DLMedia desktop entry + icon for the current user,
# so "DLMedia" shows up in the GNOME/KDE/etc. application menu and launches the TUI.
#
#   ./install-desktop.sh              install
#   ./install-desktop.sh --uninstall  remove
#
# No root needed — everything goes under $XDG_DATA_HOME (~/.local/share).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
apps="$data/applications"
icondir="$data/icons/hicolor/scalable/apps"
desktop="$apps/dlmedia.desktop"
icon="$icondir/dlmedia.svg"

if [[ "${1:-}" == "--uninstall" ]]; then
    rm -f "$desktop" "$icon"
    echo "Removed DLMedia desktop entry and icon."
else
    mkdir -p "$apps" "$icondir"
    install -m644 "$HERE/assets/dlmedia.svg" "$icon"
    sed "s|__DLMEDIA_EXEC__|$HERE/dlmedia|" "$HERE/dlmedia.desktop" > "$desktop"
    chmod 644 "$desktop"
    chmod +x "$HERE/dlmedia"
    echo "Installed: $desktop"
    echo "Look for 'DLMedia' in your application menu (it opens the TUI in a terminal)."
fi

# Refresh caches if the tools are present (harmless if not).
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$apps" 2>/dev/null || true
command -v gtk-update-icon-cache  >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$data/icons/hicolor" 2>/dev/null || true

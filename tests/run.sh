#!/usr/bin/env bash
# dlmedia test suite — exercises the non-interactive functions (build_yt_args,
# cli_main, load_lang) and locale parity. The dialog TUI can't be tested here
# (every screen blocks on `dialog`); this covers everything that doesn't.
#
# Run:  bash tests/run.sh        (or: ./tests/run.sh)
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DLMEDIA="$HERE/../dlmedia"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Load just the functions (no app runtime).
DLMEDIA_LIB=1 source "$DLMEDIA"

pass=0; fail=0
eq()       { if [[ "$2" == "$3" ]]; then echo "  ✓ $1"; ((pass++)); else echo "  ✗ $1"; printf '     expected: [%s]\n     got:      [%s]\n' "$3" "$2"; ((fail++)); fi; }
has()      { if [[ "$2" == *"$3"* ]]; then echo "  ✓ $1"; ((pass++)); else echo "  ✗ $1 (missing substring: $3)"; printf '     got: [%s]\n' "$2"; ((fail++)); fi; }
section()  { echo; echo "── $1"; }

# Stubs so cli_main's downloader calls are observable, not real. A bash function
# shadows the PATH binary for both `command -v` and invocation.
yt-dlp() { printf 'YTDLP'; local a; for a in "$@"; do printf ' %s' "$a"; done; printf '\n'; }
spotdl() { printf 'SPOTDL'; local a; for a in "$@"; do printf ' %s' "$a"; done; printf '\n'; }

export DOWNLOAD_DIR="$TMP/dl"
export DEFAULT_FORMAT="" DEFAULT_QUALITY=""

section "load_lang / i18n"
UI_LANG=en load_lang; eq  "en: btn_download"      "${M[btn_download]}" "Download"
                      eq  "en: key count >= 70"   "$([[ ${#M[@]} -ge 70 ]] && echo ok)" "ok"
UI_LANG=pl load_lang; eq  "pl: btn_download"      "${M[btn_download]}" "Pobierz"
UI_LANG=zz load_lang; eq  "missing lang -> en"    "${M[btn_download]}" "Download"
                      has "template has %s"        "${M[preview_body]}" "%s"

section "build_yt_args"
build_yt_args mp4 best; eq "mp4/best"   "${args[*]}" "-f bestvideo+bestaudio/best --merge-output-format mp4"
build_yt_args mp4 720;  has "mp4/720 caps height" "${args[*]}" "height<=720"
build_yt_args mp4 720;  has "mp4/720 merges mp4"  "${args[*]}" "--merge-output-format mp4"
build_yt_args mp4 2160; has "mp4/4K caps height"  "${args[*]}" "height<=2160"
build_yt_args mp4 2160; eq  "mp4/4K not mp4-capped" "$([[ "${args[*]}" != *'[ext=mp4]'* ]] && echo ok)" "ok"
build_yt_args mp3 320;  eq "mp3/320"    "${args[*]}" "-x --audio-format mp3 --audio-quality 320K"
build_yt_args mp3 128;  eq "mp3/128"    "${args[*]}" "-x --audio-format mp3 --audio-quality 128K"

section "cli_main — validation (run in subshell; die calls exit)"
UI_LANG=en load_lang
out=$(cli_main --format mp3 2>&1);                     eq "no --url exits 1" "$?" "1"; has "  message" "$out" "No URL"
out=$(cli_main --url http://x --format ogg 2>&1);      eq "bad format exits 1" "$?" "1"; has "  message" "$out" "mp3 or mp4"
out=$(cli_main --frobnicate 2>&1);                     eq "unknown arg exits 1" "$?" "1"; has "  message" "$out" "--frobnicate"

section "cli_main — YouTube routing (stubbed yt-dlp)"
out=$(cli_main --url 'https://youtu.be/abc' --format mp3 --quality 192 --out "$TMP/o" 2>&1)
has "calls yt-dlp"            "$out" "YTDLP"
has "passes audio quality"   "$out" "--audio-quality 192K"
has "output template + --out" "$out" "-o $TMP/o/%(title)s.%(ext)s"
out=$(cli_main --url 'https://youtu.be/abc' --format mp4 --out "$TMP/o" 2>&1)
has "mp4 default quality=best" "$out" "bestvideo+bestaudio/best"

section "cli_main — Spotify routing (stubbed spotdl)"
out=$(cli_main --url 'https://open.spotify.com/track/xyz' --out "$TMP/o" 2>&1)
has "calls spotdl"           "$out" "SPOTDL"
has "default bitrate 320k"   "$out" "--bitrate 320k"
has "spotdl output template" "$out" "{artist} - {title}"

section "locale parity"
parity=$(python3 - "$HERE/.." <<'PY'
import json, re, glob, sys, os
root = sys.argv[1]
locs = {f: set(json.load(open(f, encoding='utf-8'))) for f in glob.glob(os.path.join(root, 'locales/*.json'))}
base = set().union(*locs.values())
prob = []
for f, ks in locs.items():
    if ks != base:
        prob.append(f"{os.path.basename(f)} missing={sorted(base-ks)} extra={sorted(ks-base)}")
used = set(re.findall(r'\$\{M\[([a-z0-9_]+)\]', open(os.path.join(root, 'dlmedia'), encoding='utf-8').read()))
for gf in glob.glob(os.path.join(root, 'gui', '*.py')):  # GUI shares the catalog: t("key")
    used |= set(re.findall(r'\bt\(\s*["\']([a-z0-9_]+)["\']', open(gf, encoding='utf-8').read()))
if used - base: prob.append(f"used-but-undefined={sorted(used-base)}")
if base - used: prob.append(f"defined-but-unused={sorted(base-used)}")
print("OK" if not prob else "; ".join(prob))
PY
)
eq "all locales same keys, all used (bash + gui)" "$parity" "OK"

section "GUI core — engine + i18n (python, no Qt)"
if python3 "$HERE/test_gui.py"; then ((pass++)); else ((fail++)); fi

echo
echo "═══ $pass passed, $fail failed ═══"
[[ $fail -eq 0 ]]

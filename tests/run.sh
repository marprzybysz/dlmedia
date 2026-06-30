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

section "nav_action / build_steps (step-machine logic)"
eq "nav 0=next"     "$(nav_action 0)"   "next"
eq "nav 3=back"     "$(nav_action 3)"   "back"
eq "nav 1=cancel"   "$(nav_action 1)"   "cancel"
eq "nav 255=exit"   "$(nav_action 255)" "exit"
eq "single ask"     "$(build_steps single true true)"    "format quality preview"
eq "single no-ask"  "$(build_steps single false false)"  "preview"
eq "single fmt-only" "$(build_steps single true false)"  "format preview"
eq "ytlist ask"     "$(build_steps ytlist true true)"    "checklist format quality"
eq "ytlist no-ask"  "$(build_steps ytlist false false)"  "checklist"
eq "spotify"        "$(build_steps spotify true true)"   "spotchecklist spotquality"
eq "sel empty=ON"   "$(sel_state 3 '')"        "ON"
eq "sel in set"     "$(sel_state 3 '1,3,5')"   "ON"
eq "sel not in set" "$(sel_state 4 '1,3,5')"   "OFF"
eq "sel no partial" "$(sel_state 1 '11,12')"   "OFF"

section "human_size (bytes -> MB/GB)"
eq "1 MiB"          "$(human_size 1048576)"    "1.0 MB"
eq "5 MiB"          "$(human_size 5242880)"    "5.0 MB"
eq "just under 1GB" "$(human_size 1073741823)" "1024.0 MB"
eq "1 GiB"          "$(human_size 1073741824)" "1.00 GB"
eq "1.5 GiB"        "$(human_size 1610612736)" "1.50 GB"
eq "NA passthrough" "$(human_size NA)"         "NA"

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

section "python suite (engine / i18n / spotdl_filter — cross-platform, no Qt)"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then ((pass++)); else ((fail++)); fi

echo
echo "═══ $pass passed, $fail failed ═══"
[[ $fail -eq 0 ]]

# Download yt-dlp.exe + ffmpeg/ffprobe into gui/bin/ so PyInstaller can bundle them
# (makes the built .exe self-contained — no tools needed on the user's PATH).
# Run on Windows from the repo root:  .\gui\fetch-tools.ps1
$ErrorActionPreference = "Stop"
$bin = Join-Path $PSScriptRoot "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null

Write-Host "Downloading yt-dlp..."
Invoke-WebRequest "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" `
    -OutFile (Join-Path $bin "yt-dlp.exe")

Write-Host "Downloading ffmpeg (essentials build)..."
$zip = Join-Path $env:TEMP "ffmpeg.zip"
$out = Join-Path $env:TEMP "ffmpeg_extract"
Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $out -Force
Get-ChildItem -Path $out -Recurse -Include ffmpeg.exe, ffprobe.exe |
    ForEach-Object { Copy-Item $_.FullName -Destination $bin -Force }
Remove-Item $zip, $out -Recurse -Force

# spotdl is a Python package (no single .exe) — for Spotify support either
#   pipx install spotdl      (the app finds it on PATH), or leave it out.

Write-Host "`nBundled tools in $bin :"
Get-ChildItem $bin | Select-Object Name, Length

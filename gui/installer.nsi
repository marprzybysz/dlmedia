; NSIS installer for DLMedia (Windows). Replaces the old Inno Setup script — same
; result: a single .exe that installs the PyInstaller one-folder build, makes shortcuts,
; registers in Add/Remove Programs, and ships a bilingual (PL/EN) wizard.
;
; Build the app FIRST:  pyinstaller gui/dlmedia.spec   ->  dist/DLMedia/
; Then run makensis FROM THIS gui/ DIRECTORY (NSIS resolves File/OutFile relative to
; the script's own dir, so we cd here to keep paths unambiguous):
;   cd gui && makensis /DMyAppVersion=1.2.3 installer.nsi
; Produces:  gui\Output\DLMedia-Setup-1.2.3.exe
; (CI does this on windows-latest — see .github/workflows/build-windows.yml.)

Unicode true
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; Version is injected by CI (makensis /DMyAppVersion=...); fallback for local builds.
!ifndef MyAppVersion
  !define MyAppVersion "0.1.0"
!endif
!define MyAppName      "DLMedia"
!define MyAppPublisher "Marcin Przybysz"
!define MyAppURL       "https://github.com/marprzybysz/dlmedia"
!define MyAppExe       "DLMedia.exe"
!define UninstKey      "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}"

Name    "${MyAppName} ${MyAppVersion}"
OutFile "Output\DLMedia-Setup-${MyAppVersion}.exe"
InstallDir "$PROGRAMFILES64\${MyAppName}"
InstallDirRegKey HKLM "Software\${MyAppName}" "InstallDir"
RequestExecutionLevel admin        ; per-machine install into Program Files

; ── Wizard pages (deliberately minimal: Welcome → Dir → Install → Finish) ───
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${MyAppExe}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Bilingual, like the old Inno build. First language listed = default.
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Polish"
!insertmacro MUI_RESERVEFILE_LANGDLL   ; keep the language picker fast under /SOLID

; ── Install ─────────────────────────────────────────────────────────────────
Section "Install"
  SetOutPath "$INSTDIR"
  ; Everything PyInstaller produced (DLMedia.exe + _internal: DLLs, locales, bin).
  ; Path is relative to this script's dir (gui/), so dist/ in the repo root is ..\dist.
  File /r "..\dist\DLMedia\*"

  CreateShortCut "$SMPROGRAMS\${MyAppName}.lnk" "$INSTDIR\${MyAppExe}"
  CreateShortCut "$DESKTOP\${MyAppName}.lnk"    "$INSTDIR\${MyAppExe}"

  ; Uninstaller + "Apps & features" / Add-Remove-Programs entry.
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr   HKLM "Software\${MyAppName}" "InstallDir" "$INSTDIR"
  WriteRegStr   HKLM "${UninstKey}" "DisplayName"     "${MyAppName}"
  WriteRegStr   HKLM "${UninstKey}" "DisplayVersion"  "${MyAppVersion}"
  WriteRegStr   HKLM "${UninstKey}" "Publisher"       "${MyAppPublisher}"
  WriteRegStr   HKLM "${UninstKey}" "URLInfoAbout"    "${MyAppURL}"
  WriteRegStr   HKLM "${UninstKey}" "DisplayIcon"     "$INSTDIR\${MyAppExe}"
  WriteRegStr   HKLM "${UninstKey}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UninstKey}" "NoModify" 1
  WriteRegDWORD HKLM "${UninstKey}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${UninstKey}" "EstimatedSize" "$0"
SectionEnd

; ── Uninstall ────────────────────────────────────────────────────────────────
Section "Uninstall"
  Delete "$SMPROGRAMS\${MyAppName}.lnk"
  Delete "$DESKTOP\${MyAppName}.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "${UninstKey}"
  DeleteRegKey HKLM "Software\${MyAppName}"
SectionEnd

; ── Init: enforce 64-bit (PySide6 is x64), 64-bit registry view, language picker ─
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "DLMedia requires 64-bit Windows."
    Abort
  ${EndIf}
  SetRegView 64
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
  SetRegView 64
FunctionEnd

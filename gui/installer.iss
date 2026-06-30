; Inno Setup script for DLMedia (Windows installer).
; Build the app FIRST (pyinstaller gui/dlmedia.spec → dist/DLMedia/), then on Windows:
;   iscc gui/installer.iss   (or open in the Inno Setup IDE and Compile)
; Produces Output/DLMedia-Setup-0.1.0.exe.

#define MyAppName "DLMedia"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Marcin Przybysz"
#define MyAppURL "https://github.com/marprzybysz/dlmedia"
#define MyAppExeName "DLMedia.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=DLMedia-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 64-bit only (PySide6 is x64)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "polish";  MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Everything PyInstaller produced in dist\DLMedia\ (the .exe + all bundled DLLs + locales).
Source: "..\dist\DLMedia\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

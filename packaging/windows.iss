#ifndef BuildVersion
  #define BuildVersion "1.2.1"
#endif
[Setup]
AppId=BRACE-Local-Research-Workbench
AppName=BRACE
AppVersion={#BuildVersion}
VersionInfoVersion=1.2.1.0
AppPublisher=BRACE contributors
AppPublisherURL=https://github.com/hasan-bukhari-dev/BRACE
AppSupportURL=https://github.com/hasan-bukhari-dev/BRACE/issues
DefaultDirName={localappdata}\Programs\BRACE
DefaultGroupName=BRACE
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
SourceDir=..
OutputDir=release-assets
OutputBaseFilename=BRACE-{#BuildVersion}-windows-x64-setup
SetupIconFile=packaging\brace.ico
UninstallDisplayIcon={app}\BRACE.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
AppComments=Local research software. Generated data remain in the user's BRACE data folder after uninstall.
[Files]
Source: "dist\BRACE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\BRACE"; Filename: "{app}\BRACE.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\BRACE"; Filename: "{app}\BRACE.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\BRACE.exe"; Description: "Open BRACE"; Flags: nowait postinstall skipifsilent

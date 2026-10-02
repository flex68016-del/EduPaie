[Setup]
AppName=EduPaie
AppVersion=0.12.0
DefaultDirName={autopf}\EduPaie
DefaultGroupName=EduPaie
OutputBaseFilename=Edupaie-Setup
Compression=lzma
SolidCompression=yes
OutputDir=installer
PrivilegesRequired=admin

[Files]
Source: "..\dist\EduPaie.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\EduPaie"; Filename: "{app}\EduPaie.exe"
Name: "{commondesktop}\EduPaie"; Filename: "{app}\EduPaie.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create desktop shortcut"; GroupDescription: "Additional shortcuts"; Flags: unchecked

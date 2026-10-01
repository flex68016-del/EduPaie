[Setup]
AppName=EduPaie
AppVersion=0.12.0
DefaultDirName={commonpf}\EduPaie
DefaultGroupName=EduPaie
OutputBaseFilename=Edupaie-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\EduPaie.exe
OutputDir=installer

[Files]
Source: "..\dist\EduPaie.exe"; DestDir="{app}"; Flags: ignoreversion
Source: "..\edupaie\db\schema.sql"; DestDir="{app}\db"; Flags: ignoreversion
Source: "..\edupaie\db\create_model_db.py"; DestDir="{app}\db"; Flags: ignoreversion

[Icons]
Name: "{group}\EduPaie"; Filename: "{app}\EduPaie.exe"
Name: "{commondesktop}\EduPaie"; Filename: "{app}\EduPaie.exe"

[Run]
Filename: "{app}\EduPaie.exe"; Description: "Lancer EduPaie"; Flags: nowait postinstall skipifsilent

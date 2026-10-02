[Setup]
AppName=EduPaie
AppVersion=0.12.0
DefaultDirName={autopf}\EduPaie
DefaultGroupName=EduPaie
OutputBaseFilename=Edupaie-Setup
Compression=lzma
SolidCompression=yes
OutputDir=installer

[Files]
Source: "..\dist\EduPaie.exe"; DestDir: "{app}"

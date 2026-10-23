#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{B7C1A2D4-5E6F-4A8B-9C0D-1E2F3A4B5C6D}
AppName=Lantern
AppVersion={#AppVersion}
AppPublisher=EnriqueBDL
DefaultDirName={autopf}\Lantern
DefaultGroupName=Lantern
OutputDir=installer
OutputBaseFilename=Lantern-Setup
SetupIconFile=control_monitores.ico
UninstallDisplayIcon={app}\Lantern.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "startup"; Description: "Iniciar Lantern con Windows"
Name: "desktopicon"; Description: "Crear icono en el escritorio"; Flags: unchecked

[Files]
Source: "dist\Lantern.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Lantern"; Filename: "{app}\Lantern.exe"
Name: "{autodesktop}\Lantern"; Filename: "{app}\Lantern.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Lantern"; ValueData: """{app}\Lantern.exe"" --background"; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\Lantern.exe"; Description: "Ejecutar Lantern"; Flags: nowait postinstall skipifsilent

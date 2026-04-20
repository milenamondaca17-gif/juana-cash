#define AppName "Juana Cash"
#define AppVersion "1.0.0"
#define AppPublisher "CAMMUS_25"
#define AppExeName "JuanaCash.exe"

[Setup]
AppId={{8F4A2B3C-1D5E-4F6A-9B0C-2E3D4F5A6B7C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\JuanaCash
DefaultGroupName={#AppName}
OutputDir=instalador_output
OutputBaseFilename=JuanaCash_Setup_v1.0
SetupIconFile=juana_cash.ico
WizardImageFile=juana_cash_wizard.bmp
WizardSmallImageFile=juana_cash_small.bmp
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el Escritorio"
Name: "startmenuicon"; Description: "Crear acceso directo en Menu Inicio"

[Files]
Source: "dist\JuanaCash\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "juana_cash.db"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "juana_cash.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\juana_cash.ico"; Tasks: desktopicon
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\juana_cash.ico"; Tasks: startmenuicon
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Ejecutar {#AppName}"; Flags: nowait postinstall skipifsilent

[Setup]
AppName=Juana Cash
AppVersion=3.8.0
AppPublisher=CAMMUS_25
DefaultDirName={autopf}\JuanaCash
DefaultGroupName=Juana Cash
OutputDir=instalador_output
OutputBaseFilename=JuanaCash_Setup
SetupIconFile=juana_cash.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=JuanaCash.exe
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones adicionales:"

[Files]
Source: "dist\JuanaCash\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.json"; DestDir: "{app}\_internal"; Flags: ignoreversion
Source: "precios_update.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "precios_update.json"; DestDir: "{app}\_internal"; Flags: ignoreversion
Source: "updater.py"; DestDir: "{app}"; Flags: ignoreversion
; Base de datos inicial con usuarios cargados (solo si no existe una ya)
Source: "juana_cash.db"; DestDir: "{userdocs}\..\JuanaCash_Data"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{userdocs}\..\JuanaCash_Data"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Juana Cash"; Filename: "{app}\JuanaCash.exe"
Name: "{group}\Desinstalar Juana Cash"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Juana Cash"; Filename: "{app}\JuanaCash.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\JuanaCash.exe"; Description: "Abrir Juana Cash"; Flags: nowait postinstall skipifsilent

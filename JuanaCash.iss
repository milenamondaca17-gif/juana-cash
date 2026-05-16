[Setup]
AppName=Juana Cash
AppVersion=4.0.5
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
Source: "whatsapp_server\server.js"; DestDir: "C:\JuanaCash\whatsapp"; Flags: ignoreversion
Source: "updater.py"; DestDir: "{app}"; Flags: ignoreversion
; Base de datos inicial con usuarios cargados (solo si no existe una ya)
Source: "juana_cash.db"; DestDir: "{userdocs}\..\JuanaCash_Data"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{userdocs}\..\JuanaCash_Data"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Juana Cash"; Filename: "{app}\JuanaCash.exe"
Name: "{group}\Desinstalar Juana Cash"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Juana Cash"; Filename: "{app}\JuanaCash.exe"; Tasks: desktopicon

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM JuanaCash.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(3000);
  Result := '';
end;

[Run]
Filename: "schtasks"; Parameters: "/delete /tn ""JuanaCash WhatsApp"" /f"; Flags: runhidden waituntilterminated; StatusMsg: "Configurando servidor WhatsApp..."
Filename: "schtasks"; Parameters: "/create /tn ""JuanaCash WhatsApp"" /tr ""cmd /c cd /d C:\JuanaCash\whatsapp && node server.js"" /sc onlogon /rl highest /f /delay 0000:30"; Flags: runhidden waituntilterminated
Filename: "{app}\JuanaCash.exe"; Description: "Abrir Juana Cash"; Flags: nowait postinstall skipifsilent

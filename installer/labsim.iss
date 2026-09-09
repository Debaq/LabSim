; Instalador Windows de LabSim (build PyInstaller onedir).
;
; Se compila en CI (.github/workflows/build-windows.yml) con:
;   ISCC /DMyAppVersion=<build_id> /DNumVersion=<x.y.z> installer\labsim.iss
; build_id puede traer sufijo de build de prueba (0.9.8-r1a2b3c4), que no
; es un numero de version valido para el VersionInfo del exe -- por eso
; NumVersion va aparte.
;
; Instalacion PER-USER a proposito (PrivilegesRequired=lowest, DefaultDirName
; en {localappdata}): sin UAC, y sobre todo porque core/updater.py reemplaza
; archivos al lado del ejecutable. En "Program Files" eso falla por permisos.

#define MyAppName "LabSim"
#define MyAppExeName "LabSim.exe"
#define MyAppPublisher "Nicolas Baier Quezada"
#define MyAppURL "https://github.com/Debaq/LabSim"

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#ifndef NumVersion
  #define NumVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\LabSim"
#endif

[Setup]
; AppId fijo: es lo que hace que una version nueva ACTUALICE la instalada
; en vez de aparecer como un segundo programa en "Aplicaciones instaladas".
; No cambiarlo nunca.
AppId={{9EBD5A50-4B31-4855-B38A-E8CFBA118B6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
VersionInfoVersion={#NumVersion}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=LabSim-windows-x86_64-setup
SetupIconFile=..\icons\Icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; El updater silencioso corre con /CLOSEAPPLICATIONS: sin esto, los DLL de
; _internal/ quedan tomados por la instancia vieja y la copia falla.
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; local_cache/ (logs.db, cola de acciones offline, layout) y json/session.json
; son data del usuario: no vienen en el build y no se tocan al actualizar.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; \
    Excludes: "resources\local_cache\*,resources\json\session.json"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Instalacion normal: casilla "Ejecutar LabSim" en la ultima pagina.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent
; Update silencioso desde el propio LabSim (updater pasa /LAUNCH=1): relanza
; la app, que es lo que el usuario espera despues de aceptar "actualizar".
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: RelanzarTrasUpdate

[UninstallDelete]
; Barrido final: data del usuario y caches de audio generados en runtime
; (_generated/, _panned/) que el instalador no puso y por lo tanto no borra.
Type: filesandordirs; Name: "{app}"

[Code]
function RelanzarTrasUpdate: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:LAUNCH|0}') = '1');
end;

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
;
; Archivo en UTF-8 con BOM (Inno Setup 6 lo lee así): lleva tildes.
;
; Con /DDelta=1 /DBaseBuildId=<build anterior> /DSourceDir=<carpeta del diff>
; sale el instalador delta de la cadena de updates (core/updater.py): solo
; trae lo que cambió respecto a BaseBuildId, borra lo que ya no existe
; (dist\delta_removed.iss, lo arma scripts/update_diff.py inno-delete) y se
; niega a correr si lo instalado no es BaseBuildId.

#define MyAppName "LabSim"
#define MyAppExeName "LabSim.exe"
#define MyAppPublisher "TecMedHub, Universidad Austral de Chile"
#define MyAppAutor "Nicolás Baier Quezada"
#define MyAppDescripcion "Simulador de laboratorio de audiología"
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
#ifdef Delta
  #ifndef BaseBuildId
    #error El instalador delta necesita /DBaseBuildId
  #endif
  #define OutputName "LabSim-windows-x86_64-update-setup"
#else
  #define OutputName "LabSim-windows-x86_64-setup"
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
AppCopyright=© 2026 {#MyAppAutor}. Desarrollado en TecMedHub, Universidad Austral de Chile
AppComments={#MyAppDescripcion}. Desarrollado en TecMedHub, Universidad Austral de Chile.
AppContact={#MyAppAutor}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
VersionInfoVersion={#NumVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador de {#MyAppName}, simulador de laboratorio de audiología
VersionInfoCopyright=© 2026 {#MyAppAutor}. Desarrollado en TecMedHub, Universidad Austral de Chile
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#NumVersion}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename={#OutputName}
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

[Messages]
; Primera página del asistente: qué es y quién lo hace.
spanish.WelcomeLabel2=Este programa instalará [name/ver] en su equipo.%n%n{#MyAppName} es un simulador de laboratorio de audiología, desarrollado en TecMedHub, Universidad Austral de Chile.%n%nAutor: {#MyAppAutor}.%n%nSe recomienda cerrar las demás aplicaciones antes de continuar.
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%n{#MyAppName} is an audiology laboratory simulator developed at TecMedHub, Universidad Austral de Chile.%n%nAuthor: {#MyAppAutor}.%n%nIt is recommended that you close all other applications before continuing.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; local_cache/ (logs.db, cola de acciones offline, layout) y json/session.json
; son data del usuario: no vienen en el build y no se tocan al actualizar.
; En el delta, __removed__.txt es la lista que se convierte en [InstallDelete].
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; \
    Excludes: "resources\local_cache\*,resources\json\session.json,__removed__.txt"

#ifdef Delta
#include "..\dist\delta_removed.iss"
#endif

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
const
  { El mismo nombre que MUTEX_NAME en src/core/updater.py: lo crea cada
    LabSim abierto. }
  MutexApp = 'LabSimAppMutex';
  { Clave de desinstalación del AppId de arriba (instalación por usuario). }
  ClaveUninstall = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{9EBD5A50-4B31-4855-B38A-E8CFBA118B6F}_is1';

function RelanzarTrasUpdate: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:LAUNCH|0}') = '1');
end;

{ El LabSim que lanzó la actualización se cierra recién después de lanzar
  este instalador: en silencio se le dan hasta 30 s para soltar sus
  archivos. A mano, se le pide al usuario que lo cierre. Si en silencio
  sigue abierto (otra ventana colgada), queda el Restart Manager
  (CloseApplications). }
function EsperarLabSimCerrado: Boolean;
var
  Vueltas: Integer;
begin
  Result := True;
  if WizardSilent then
  begin
    Vueltas := 0;
    while CheckForMutexes(MutexApp) and (Vueltas < 60) do
    begin
      Sleep(500);
      Vueltas := Vueltas + 1;
    end;
    if CheckForMutexes(MutexApp) then
      Log('LabSim sigue abierto tras 30 s: queda el Restart Manager');
  end
  else
    while CheckForMutexes(MutexApp) do
      if MsgBox('LabSim está abierto. Ciérralo y pulsa Aceptar para continuar.',
                mbError, MB_OKCANCEL) = IDCANCEL then
      begin
        Result := False;
        Exit;
      end;
end;

#ifdef Delta
{ Lo que dice BUILD_VERSION en la carpeta instalada, o '' si no hay
  LabSim instalado. }
function VersionInstalada: String;
var
  Carpeta: String;
  Contenido: AnsiString;
begin
  Result := '';
  if RegQueryStringValue(HKCU, ClaveUninstall, 'InstallLocation', Carpeta) then
    if LoadStringFromFile(AddBackslash(Carpeta) + 'BUILD_VERSION', Contenido) then
      Result := Trim(String(Contenido));
end;
#endif

function InitializeSetup: Boolean;
#ifdef Delta
var
  Instalada: String;
#endif
begin
#ifdef Delta
  { Un delta sobre otra versión dejaría una mezcla de archivos: se corta
    antes de tocar nada. El updater cae al instalador completo. }
  Instalada := VersionInstalada;
  if Instalada <> '{#BaseBuildId}' then
  begin
    Log('Delta para {#BaseBuildId}, instalada: "' + Instalada + '"');
    if not WizardSilent then
      MsgBox('Este instalador solo actualiza LabSim {#BaseBuildId} y la versión instalada es "' +
             Instalada + '". Descarga LabSim-windows-x86_64-setup.exe.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
#endif
  Result := EsperarLabSimCerrado;
end;

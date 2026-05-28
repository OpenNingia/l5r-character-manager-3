; Per-user installer variant — installs without administrator rights.
; Mirrors setup.iss but targets {userpf}, HKCU, and {userfonts}; uses a
; distinct AppId and OutputBaseFilename so it can coexist with the
; system-wide installer.
#define MyAppName      "L5R: CM"
#define MyAppPublisher "OpenNingia"

; AppVer is passed in by ISCC via `/DAppVer=X.Y.Z`, driven from
; l5r.l5rcmcore.APP_VERSION in the GitHub Actions workflow. The fallback
; keeps local ISCC runs working.
#ifndef AppVer
  #define AppVer "0.0.0-dev"
#endif

[Setup]
; Distinct AppId so the per-user install is tracked separately from the
; system-wide install (allowing both to coexist on a machine).
AppId={{bcd5e388-9c29-44a0-bab9-c6dece846aae}
AppName=L5R 4E: Character Manager (User)
AppVersion={#AppVer}
AppVerName={#MyAppName} {#AppVer}
AppPublisher={#MyAppPublisher}
; Install without elevation, per-user only.
PrivilegesRequired=lowest
DefaultDirName={userpf}\openningia\l5rcm
DefaultGroupName=OpenNingia\L5RCM
UninstallDisplayIcon={app}\l5rcm.exe
SetupIconFile=l5rcm.ico
Compression=lzma2
SolidCompression=yes
OutputBaseFilename=l5rcm-setup-user
WizardImageFile=banner_l.bmp
WizardSmallImageFile=setup_icon.bmp
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist/*"; DestDir: "{app}"; Flags: recursesubdirs;
; Place all common files here, first one should be marked 'solidbreak'
Source: "common/*";  DestDir: "{app}"; Flags: solidbreak recursesubdirs
; Fonts install per-user ({userfonts}) — no admin rights required.
Source: "fonts/OLDSSCH_.TTF"; DestDir: "{userfonts}"; FontInstall: "Oldstyle Small Caps"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontOldStyle
Source: "fonts/OLDSIH__.TTF"; DestDir: "{userfonts}"; FontInstall: "Oldstyle Italic"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontOldStyle
Source: "fonts/OLDSH___.TTF"; DestDir: "{userfonts}"; FontInstall: "Oldstyle 1"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontOldStyle
Source: "fonts/LiberationSans-Regular.ttf"; DestDir: "{userfonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations
Source: "fonts/LiberationSans-Italic.ttf"; DestDir: "{userfonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations
Source: "fonts/LiberationSans-BoldItalic.ttf"; DestDir: "{userfonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations
Source: "fonts/LiberationSans-Bold.ttf"; DestDir: "{userfonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations
; core pack
Source: "core.l5rcmpack"; DestDir: "{app}";

[Icons]
Name: "{group}\L5RCM"; Filename: "{app}\l5rcm.exe"


[Tasks]
Name: l5rAssociation; Description: "Associate ""Character files (.l5r)"" extension"; GroupDescription: File extensions:
Name: l5rpackAssociation; Description: "Associate ""Datapack files (.l5rcmpack)"" extension"; GroupDescription: File extensions:
; fonts
Name: fontLiberations; Description: "Install ""Liberation Sans"" fonts (current user)"; GroupDescription: Fonts:
Name: fontOldStyle; Description: "Install ""Old Style"" fonts (current user)"; GroupDescription: Fonts:
; core pack
Name: importCorePack; Description: "Install Core Datapack"; GroupDescription: Data:

[Registry]
; File associations written under HKCU\Software\Classes — the per-user
; equivalent of HKCR. No admin rights needed; Windows merges these into
; the effective HKCR view for the current user.
; extensions
Root: HKCU; Subkey: "Software\Classes\.l5r"; ValueType: string; ValueName: ""; ValueData: "L5Rcm.Character"; Flags: uninsdeletevalue; Tasks: l5rAssociation
Root: HKCU; Subkey: "Software\Classes\.l5rcmpack"; ValueType: string; ValueName: ""; ValueData: "L5Rcm.Pack"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation
; icons
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Character\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{code:GetShortName|{app}}\l5rcm.exe,0"; Flags: uninsdeletevalue; Tasks: l5rAssociation
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Pack\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{code:GetShortName|{app}}\l5rcm.exe,1"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation
; names
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Character"; ValueType: string; ValueName: ""; ValueData: "L5R: CM - Character File"; Flags: uninsdeletevalue; Tasks: l5rAssociation
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Pack"; ValueType: string; ValueName: ""; ValueData: "L5R: CM - Data Pack File"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation
; verbs
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Character\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\l5rcm.exe"" --open ""%1"""; Flags: uninsdeletevalue; Tasks: l5rAssociation
Root: HKCU; Subkey: "Software\Classes\L5Rcm.Pack\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\l5rcm.exe"" --import ""%1"""; Flags: uninsdeletevalue; Tasks: l5rpackAssociation

[Run]
Filename: "{app}\l5rcm.exe"; Parameters: "--import ""{app}\core.l5rcmpack"""; Tasks: importCorePack

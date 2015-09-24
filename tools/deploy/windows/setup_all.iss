; -- 64BitTwoArch.iss --
; Demonstrates how to install a program built for two different
; architectures (x86 and x64) using a single installer.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!
#define ExeVer GetFileVersion('bin_x64/main.exe')

[Setup]
AppName=L5R 4E: Character Manager
AppVersion={#ExeVer}
DefaultDirName={pf}\openningia\l5rcm
DefaultGroupName=OpenNingia\L5RCM
UninstallDisplayIcon={app}\main.exe
SetupIconFile=l5rcm.ico
Compression=lzma2
SolidCompression=yes
OutputBaseFilename=l5rcm-{#ExeVer}
WizardImageFile=banner_l.bmp
WizardSmallImageFile=setup_icon.bmp
;OutputDir=l5rcm-{AppVersion}
; "ArchitecturesInstallIn64BitMode=x64" requests that the install be
; done in "64-bit mode" on x64, meaning it should use the native
; 64-bit Program Files directory and the 64-bit view of the registry.
; On all other architectures it will install in "32-bit mode".
ArchitecturesInstallIn64BitMode=x64
; Note: We don't set ProcessorsAllowed because we want this
; installation to run on all architectures (including Itanium,
; since it's capable of running 32-bit code too).

[Files]
; Install MyProg-x64.exe if running in 64-bit mode (x64; see above),
; MyProg.exe otherwise.
; Place all x64 files here
Source: "bin_x64/*"; DestDir: "{app}"; Check: Is64BitInstallMode;
; Place all x86 files here, first one should be marked 'solidbreak'
Source: "bin_x86/*"; DestDir: "{app}"; Check: not Is64BitInstallMode; Flags: solidbreak
; Place all common files here, first one should be marked 'solidbreak'
Source: "common/*";  DestDir: "{app}"; Flags: solidbreak recursesubdirs
; Source: "MyProg.chm"; DestDir: "{app}"; Flags: solidbreak
; Source: "Readme.txt"; DestDir: "{app}"; Flags: isreadme
Source: "fonts/OLDSSCH_.TTF"; DestDir: "{fonts}"; FontInstall: "Oldstyle Small Caps"; Flags: uninsneveruninstall; Tasks: fontOldStyle 
Source: "fonts/OLDSIH__.TTF"; DestDir: "{fonts}"; FontInstall: "Oldstyle Italic"; Flags: uninsneveruninstall; Tasks: fontOldStyle 
Source: "fonts/OLDSH___.TTF"; DestDir: "{fonts}"; FontInstall: "Oldstyle 1"; Flags: uninsneveruninstall; Tasks: fontOldStyle 
Source: "fonts/LiberationSans-Regular.ttf"; DestDir: "{fonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations 
Source: "fonts/LiberationSans-Italic.ttf"; DestDir: "{fonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations 
Source: "fonts/LiberationSans-BoldItalic.ttf"; DestDir: "{fonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations 
Source: "fonts/LiberationSans-Bold.ttf"; DestDir: "{fonts}"; FontInstall: "Liberation Sans"; Flags: onlyifdoesntexist uninsneveruninstall; Tasks: fontLiberations 
; core pack
Source: "core.l5rcmpack"; DestDir: "{app}";

[Icons]
Name: "{group}\L5RCM"; Filename: "{app}\main.exe"


[Tasks]
Name: l5rAssociation; Description: "Associate ""Character files (.l5r)"" extension"; GroupDescription: File extensions:
Name: l5rpackAssociation; Description: "Associate ""Datapack files (.l5rcmpack)"" extension"; GroupDescription: File extensions:
; fonts
Name: fontLiberations; Description: "Install ""Liberation Sans"" fonts"; GroupDescription: Fonts:
Name: fontOldStyle; Description: "Install ""Old Style"" fonts"; GroupDescription: Fonts:
; core pack
Name: importCorePack; Description: "Install Core Datapack"; GroupDescription: Data:

[Registry]
; extensions
Root: HKCR; Subkey: ".l5r"; ValueType: string; ValueName: ""; ValueData: "L5Rcm.Character"; Flags: uninsdeletevalue; Tasks: l5rAssociation 
Root: HKCR; Subkey: ".l5rcmpack"; ValueType: string; ValueName: ""; ValueData: "L5Rcm.Pack"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation 
; names
Root: HKCR; Subkey: "L5Rcm.Character"; ValueType: string; ValueName: ""; ValueData: "{app}\main.exe,0"; Flags: uninsdeletevalue; Tasks: l5rAssociation 
Root: HKCR; Subkey: "L5Rcm.Pack"; ValueType: string; ValueName: ""; ValueData: "{app}\main.exe,1"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation 
; icons
Root: HKCR; Subkey: "L5Rcm.Character\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "L5R: CM - Character File"; Flags: uninsdeletevalue; Tasks: l5rAssociation 
Root: HKCR; Subkey: "L5Rcm.Pack\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "L5R: CM - Data Pack File"; Flags: uninsdeletevalue; Tasks: l5rpackAssociation 
; verbs
Root: HKCR; Subkey: "L5Rcm.Character\shell\open\command"; ValueType: string; ValueName: ""; ValueData: "\""{app}\main.exe\"" --open \""%1\"""; Flags: uninsdeletevalue; Tasks: l5rAssociation 
Root: HKCR; Subkey: "L5Rcm.Pack\shell\open\command"; ValueType: string; ValueName: ""; ValueData: "\""{app}\main.exe\"" --import \""%1\"""; Flags: uninsdeletevalue; Tasks: l5rpackAssociation 

[Run]
Filename: "{app}\main.exe"; Parameters: "--import ""{app}""\core.l5rcmpack"; Tasks: importCorePack 

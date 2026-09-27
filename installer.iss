#define AppVersion "1.0.0"
[Setup]
AppId={{AB4A8B1B-C79D-432A-86C6-A2D557290811}
AppName=ImageToPDF
AppVersion={#AppVersion}
AppPublisher=yjw071218
AppPublisherURL=https://github.com/yjw071218/image-to-pdf
AppSupportURL=https://github.com/yjw071218/image-to-pdf/issues
DefaultDirName={localappdata}\Programs\ImageToPDF
DefaultGroupName=ImageToPDF
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=release
OutputBaseFilename=ImageToPDF-Setup-{#AppVersion}-x64
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\ImageToPDF.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
LicenseFile=LICENSE
ChangesAssociations=yes
CloseApplications=yes
AppMutex=Local\ImageToPDF_v1

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\ImageToPDF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ImageToPDF"; Filename: "{app}\ImageToPDF.exe"
Name: "{autodesktop}\이미지를 PDF로 엮기"; Filename: "{app}\ImageToPDF.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.bmp\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.gif\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.gif\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.gif\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.gif\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tif\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.tiff\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\ImageToPDF_ME"; ValueType: string; ValueName: ""; ValueData: "이미지를 PDF로 엮기"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\ImageToPDF_ME"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\ImageToPDF_ME"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\ImageToPDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shell\ImageToPDF_ME\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ImageToPDF.exe"" ""%1"""

[Run]
Filename: "{app}\ImageToPDF.exe"; Description: "ImageToPDF 실행"; Flags: nowait postinstall skipifsilent

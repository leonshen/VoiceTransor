; VoiceTransor Inno Setup Script
; Creates a Windows installer for VoiceTransor
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "VoiceTransor"
#define MyAppVersion "0.9.0"
#define MyAppPublisher "VoiceTransor"
#define MyAppURL "https://github.com/leonshen/VoiceTransor"
#define MyAppExeName "VoiceTransor.exe"
#define MyAppDescription "AI-Powered Speech-to-Text with Local Processing"

[Setup]
; Basic App Information
AppId={{VOICETRANSOR-1234-5678-9ABC-DEF012345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppComments={#MyAppDescription}

; Installation Directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=..\dist\installer_output
OutputBaseFilename=VoiceTransor-v0.9.0-Windows-x64-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=2

; Requirements
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Visual Style
WizardStyle=modern
WizardSizePercent=100,100
DisableWelcomePage=no

; License (optional - uncomment if you have a license file)
; LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
; Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main Application
Source: "..\dist\VoiceTransor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\docs\zh-CN\README.md"; DestDir: "{app}"; DestName: "README_zh_CN.md"; Flags: ignoreversion
Source: "..\docs\INSTALLATION.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\zh-CN\INSTALLATION.md"; DestDir: "{app}"; DestName: "INSTALLATION_zh_CN.md"; Flags: ignoreversion
Source: "..\docs\USER_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion

; Helper Scripts (if exist)
Source: "..\scripts\setup\install_ollama.bat"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{#SourcePath}\..\scripts\setup\install_ollama.bat'))

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\USER_GUIDE.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop Icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch Icon (only in non-admin mode to avoid userappdata warning)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; Check: not IsAdminInstallMode

[Run]
; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Option to view installation guide
Filename: "{app}\INSTALLATION.md"; Description: "View Installation Guide"; Flags: postinstall shellexec skipifsilent unchecked

[Code]
var
  FFmpegPage: TInputOptionWizardPage;
  OllamaPage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  { Create custom page for FFmpeg information }
  FFmpegPage := CreateInputOptionPage(wpSelectTasks,
    'Required: FFmpeg Installation',
    'VoiceTransor requires FFmpeg to process audio files',
    'FFmpeg is not included in this installer. You must install it separately.' + #13#10 + #13#10 +
    'Installation steps:' + #13#10 +
    '1. Download from: https://www.gyan.dev/ffmpeg/builds/' + #13#10 +
    '2. Choose "ffmpeg-release-essentials.zip"' + #13#10 +
    '3. Extract to C:\ffmpeg' + #13#10 +
    '4. Add C:\ffmpeg\bin to your PATH' + #13#10 + #13#10 +
    'For detailed instructions, see INSTALLATION.md after setup completes.',
    False, False);
  FFmpegPage.Add('I understand that I need to install FFmpeg separately');
  FFmpegPage.Values[0] := True;

  { Create custom page for Ollama information }
  OllamaPage := CreateInputOptionPage(FFmpegPage.ID,
    'Optional: Ollama for AI Text Processing',
    'Install Ollama to enable AI-powered text features',
    'Ollama enables features like summarize, translate, and custom text processing.' + #13#10 + #13#10 +
    'Installation is optional but recommended:' + #13#10 +
    '1. Download from: https://ollama.com/download' + #13#10 +
    '2. Run the installer' + #13#10 +
    '3. Open terminal and run: ollama pull llama3.1:8b' + #13#10 + #13#10 +
    'You can also use install_ollama.bat in the installation folder.',
    False, False);
  OllamaPage.Add('I want to install Ollama for AI text processing features');
  OllamaPage.Values[0] := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  { Validate FFmpeg acknowledgment }
  if CurPageID = FFmpegPage.ID then
  begin
    if not FFmpegPage.Values[0] then
    begin
      MsgBox('Please acknowledge that you need to install FFmpeg.' + #13#10 + #13#10 +
             'VoiceTransor will not work without FFmpeg.',
             mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Create quick start shortcut }
    SaveStringToFile(ExpandConstant('{app}\QUICK_START.txt'),
      'VoiceTransor - Quick Start' + #13#10 +
      '===========================' + #13#10 +
      '' + #13#10 +
      '1. INSTALL FFMPEG (Required)' + #13#10 +
      '   See INSTALLATION.md for detailed steps' + #13#10 +
      '' + #13#10 +
      '2. RUN APPLICATION' + #13#10 +
      '   Use the desktop shortcut or Start Menu' + #13#10 +
      '' + #13#10 +
      '3. OPTIONAL: Install Ollama' + #13#10 +
      '   Download: https://ollama.com/download' + #13#10 +
      '' + #13#10 +
      'For full documentation, see README.md' + #13#10 +
      '' + #13#10 +
      'Support: voicetransor@gmail.com',
      False);
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\*.log"
Type: filesandordirs; Name: "{app}\temp"

[Messages]
WelcomeLabel1=Welcome to [name] Setup
WelcomeLabel2=This will install [name/ver] on your computer.%n%nVoiceTransor is an AI-powered speech-to-text application that runs completely on your local machine.%n%nYour data stays private - no cloud processing required.
FinishedHeadingLabel=Completing [name] Setup
FinishedLabelNoIcons=Setup has installed [name] on your computer.%n%nIMPORTANT: You must install FFmpeg separately before using VoiceTransor.%n%nSee INSTALLATION.md in the installation folder for detailed instructions.

@echo off
REM Ollama Installation Script for VoiceTransor
REM This script helps users install Ollama on Windows

setlocal enabledelayedexpansion

echo ========================================
echo Ollama Installation for VoiceTransor
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges.
) else (
    echo [WARNING] Not running as administrator.
    echo Some features may require admin rights.
    echo.
)

REM Check if Ollama is already installed
where ollama >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Ollama is already installed!
    echo.
    ollama --version
    echo.
    goto :check_service
)

echo [INFO] Ollama is not installed. Starting installation...
echo.

REM Set download URL
set OLLAMA_URL=https://ollama.com/download/OllamaSetup.exe
set INSTALLER_PATH=%TEMP%\OllamaSetup.exe

echo [INFO] Downloading Ollama installer...
echo URL: %OLLAMA_URL%
echo.

REM Download using PowerShell
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%OLLAMA_URL%' -OutFile '%INSTALLER_PATH%'}"

if not exist "%INSTALLER_PATH%" (
    echo.
    echo [ERROR] Failed to download Ollama installer.
    echo.
    echo Please download manually from: https://ollama.com/download
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Download completed: %INSTALLER_PATH%
echo.
echo [INFO] Starting installation...
echo Please follow the installer instructions.
echo.

REM Run the installer
start /wait "" "%INSTALLER_PATH%"

REM Check if installation succeeded
where ollama >nul 2>&1
if %errorLevel% == 0 (
    echo.
    echo [OK] Ollama has been installed successfully!
    echo.
    ollama --version
) else (
    echo.
    echo [WARNING] Ollama command not found after installation.
    echo You may need to restart your terminal or computer.
    echo.
)

REM Clean up
del "%INSTALLER_PATH%" >nul 2>&1

:check_service
echo.
echo ========================================
echo Checking Ollama Service
echo ========================================
echo.

REM Check if Ollama service is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Ollama service is running!
    echo.
    goto :pull_model
) else (
    echo [INFO] Ollama service is not running.
    echo.
    echo Starting Ollama service...
    echo.
    start "" ollama serve
    timeout /t 3 >nul
    echo [OK] Ollama service started in background.
    echo.
)

:pull_model
echo ========================================
echo Downloading Recommended Model
echo ========================================
echo.
echo Recommended model: llama3.1:8b
echo - Size: ~4.7GB
echo - RAM: 8GB recommended
echo - Good balance of speed and quality
echo.

set PULL_MODEL=Y
set /p PULL_MODEL="Download llama3.1:8b now? (Y/N, default=Y): "
if /i "%PULL_MODEL%"=="" set PULL_MODEL=Y

if /i "%PULL_MODEL%"=="Y" (
    echo.
    echo [INFO] Downloading llama3.1:8b...
    echo This may take several minutes depending on your internet speed.
    echo.
    ollama pull llama3.1:8b
    echo.
    if %errorLevel% == 0 (
        echo [OK] Model llama3.1:8b downloaded successfully!
    ) else (
        echo [WARNING] Failed to download model. You can try again later:
        echo     ollama pull llama3.1:8b
    )
) else (
    echo.
    echo [INFO] Skipping model download.
    echo You can download models later with:
    echo     ollama pull llama3.1:8b
    echo     ollama pull qwen2.5:7b
    echo     ollama pull gemma2:9b
)

echo.
echo ========================================
echo Installation Summary
echo ========================================
echo.

REM List installed models
echo Installed models:
ollama list 2>NUL
if %errorLevel% neq 0 (
    echo   (No models installed yet)
)

echo.
echo ========================================
echo Next Steps
echo ========================================
echo.
echo 1. Ollama is now ready to use!
echo 2. Make sure Ollama service is running (started automatically)
echo 3. Open VoiceTransor and try "Run Text Operations"
echo.
echo Useful commands:
echo   ollama serve          - Start Ollama service
echo   ollama list           - List installed models
echo   ollama pull [model]   - Download a model
echo   ollama rm [model]     - Remove a model
echo.
echo For more information, visit: https://ollama.com
echo.
echo ========================================

pause

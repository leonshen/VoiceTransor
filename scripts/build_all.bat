@echo off
REM VoiceTransor - Complete Build and Packaging Script
REM This script performs all build steps in one go:
REM 1. Build application with PyInstaller
REM 2. Package distribution (ZIP)
REM 3. Create installer with Inno Setup

echo ========================================
echo VoiceTransor - Complete Build Pipeline
echo ========================================
echo.
echo This script will:
echo   1. Build application executable
echo   2. Create distribution package
echo   3. Generate Windows installer
echo.
echo Estimated time: 10-15 minutes
echo.
pause

REM Step 1: Build Application
echo.
echo ========================================
echo Step 1/3: Building Application
echo ========================================
echo.
call scripts\build\build_app.bat
if errorlevel 1 (
    echo.
    echo [ERROR] Application build failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Application built successfully!
echo.

REM Step 2: Package Distribution
echo.
echo ========================================
echo Step 2/3: Creating Distribution Package
echo ========================================
echo.
call scripts\build\package_distribution.bat
if errorlevel 1 (
    echo.
    echo [ERROR] Distribution packaging failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Distribution package created!
echo.

REM Step 3: Create Installer (Check if Inno Setup is available)
echo.
echo ========================================
echo Step 3/3: Creating Windows Installer
echo ========================================
echo.

REM Check if iscc is available
where iscc >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Inno Setup Compiler (iscc) not found in PATH!
    echo.
    echo Please install Inno Setup from: https://jrsoftware.org/isinfo.php
    echo Or add iscc.exe to your PATH.
    echo.
    echo Skipping installer creation...
    goto :skip_installer
)

echo [INFO] Running Inno Setup Compiler...
echo.
iscc installer\installer.iss
if errorlevel 1 (
    echo.
    echo [ERROR] Installer creation failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Installer created successfully!
goto :installer_done

:skip_installer
echo [INFO] Installer creation skipped.

:installer_done
echo.
echo ========================================
echo Build Pipeline Complete!
echo ========================================
echo.
echo Output locations:
echo   - Application:   dist\VoiceTransor\VoiceTransor.exe
echo   - Package:       dist\VoiceTransor-v0.9.0-Windows-x64\
echo   - ZIP:           dist\VoiceTransor-v0.9.0-Windows-x64.zip (if created)
echo   - Installer:     dist\installer_output\VoiceTransor-v0.9.0-Windows-x64-Setup.exe
echo.
echo Next steps:
echo   1. Test the built application
echo   2. Test the installer on a clean machine
echo   3. Upload to GitHub Releases or distribution server
echo.
echo ========================================

pause

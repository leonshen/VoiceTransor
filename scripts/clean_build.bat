@echo off
REM Clean build artifacts and temporary files

echo ========================================
echo Cleaning Build Artifacts
echo ========================================
echo.

if exist build (
    echo [INFO] Removing build\ directory...
    rmdir /s /q build
)

if exist dist (
    echo [INFO] Removing dist\ directory...
    rmdir /s /q dist
)

if exist *.spec~ (
    echo [INFO] Removing backup spec files...
    del /q *.spec~
)

echo.
echo [SUCCESS] Build artifacts cleaned!
echo.
pause

# VoiceTransor Build Instructions

This document explains how to package VoiceTransor into standalone executables for end users who don't have Python installed.

## 📋 Prerequisites

### All Platforms
- Python 3.8+
- All project dependencies installed: `pip install -r requirements.txt`
- PyInstaller: `pip install pyinstaller`

### Windows
- Optional: Inno Setup (for creating installers)

### macOS
- Optional: `create-dmg` (for creating DMG installers): `brew install create-dmg`

## 🔨 Quick Build

### Windows

```bash
# Method 1: Use build script (recommended)
scripts\build\build_app.bat

# Method 2: Manual build
pyinstaller VoiceTransor.spec
```

**Output location:** `dist\VoiceTransor\VoiceTransor.exe`

### macOS

```bash
# Add execute permission to the script
chmod +x scripts/build/build_app.sh

# Method 1: Use build script (recommended)
./scripts/build/build_app.sh

# Method 2: Manual build
pyinstaller VoiceTransor.spec
```

**Output location:** `dist/VoiceTransor.app`

## 📦 Detailed Steps

### 1. Clean Previous Builds

```bash
# Windows
rmdir /s /q build dist

# macOS/Linux
rm -rf build dist
```

### 2. Run PyInstaller

```bash
pyinstaller VoiceTransor.spec
```

The build process may take 5-10 minutes depending on your machine.

### 3. Test the Executable

**Windows:**
```bash
dist\VoiceTransor\VoiceTransor.exe
```

**macOS:**
```bash
open dist/VoiceTransor.app
```

## 📌 Important Notes

### ⚠️ External Dependencies

VoiceTransor requires the following external programs (not bundled):

1. **ffmpeg / ffprobe** - Audio processing
   - Windows: Download and add to PATH
   - macOS: `brew install ffmpeg`

2. **Ollama** (optional) - Local LLM
   - Users need to install separately
   - Provide `scripts/setup/install_ollama.bat` (Windows) and `scripts/setup/install_ollama.sh` (macOS)

3. **Whisper Models**
   - Downloaded automatically on first run
   - Requires internet connection

### 📂 Bundled Resources

The packaged app includes:
- ✅ Translation files (`*.qm`, `*.ts`)
- ✅ Whisper module data
- ❌ **NOT included:** Whisper model files (too large, downloaded at runtime)

### 🔧 Troubleshooting

#### Issue: App fails to start after packaging

**Solution:**
1. Verify all dependencies are installed in your Python environment
2. Check `build/VoiceTransor/warn-VoiceTransor.txt` for warnings
3. Try debug mode:
   ```bash
   pyinstaller --debug=all VoiceTransor.spec
   ```

#### Issue: Translation files missing

**Solution:**
Ensure `.qm` files exist and are correctly configured in spec file:
```python
datas = [
    ('app/i18n/locales/*.qm', 'app/i18n/locales'),
]
```

#### Issue: Executable is too large

**Solution:**
1. Exclude unnecessary modules in spec file:
   ```python
   excludes=['matplotlib', 'scipy', 'pandas']
   ```

2. Use UPX compression (already enabled in spec)

3. Consider `--onefile` mode (slower startup)

## 📦 Creating Installers

### Windows - Inno Setup

1. Download and install [Inno Setup](https://jrsoftware.org/isinfo.php)

2. Create `installer.iss` file:

```iss
[Setup]
AppName=VoiceTransor
AppVersion=1.0.0
DefaultDirName={pf}\VoiceTransor
DefaultGroupName=VoiceTransor
OutputDir=..\dist\installer_output
OutputBaseFilename=VoiceTransor_Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "..\dist\VoiceTransor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\VoiceTransor"; Filename: "{app}\VoiceTransor.exe"
Name: "{commondesktop}\VoiceTransor"; Filename: "{app}\VoiceTransor.exe"
```

3. Compile from project root:
   ```bash
   iscc installer\installer.iss
   ```
   Output: `dist\installer_output\VoiceTransor_Setup.exe`

### macOS - DMG

```bash
create-dmg \
  --volname "VoiceTransor" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "VoiceTransor.app" 175 120 \
  --app-drop-link 425 120 \
  "VoiceTransor.dmg" \
  "dist/"
```

## 🚀 Distribution

### Distribution Package Contents

**Windows package should include:**
- ✅ `VoiceTransor.exe` (or installer)
- ✅ `README.md` (user manual)
- ✅ `scripts/setup/install_ollama.bat` (optional)
- ✅ Instructions for ffmpeg installation

**macOS package should include:**
- ✅ `VoiceTransor.app` (or DMG)
- ✅ `README.md` (user manual)
- ✅ `scripts/setup/install_ollama.sh` (optional)
- ✅ Instructions for ffmpeg installation (Homebrew)

### User Installation Guide

Include in your distribution:

1. **System Requirements**
   - Windows 10+ / macOS 10.15+
   - 8GB+ RAM (recommended)
   - 5GB+ disk space (for models)

2. **First-Time Setup**
   - Install ffmpeg
   - (Optional) Install Ollama
   - Run the application
   - First transcription will download Whisper models

3. **Troubleshooting**
   - Antivirus may flag the app (Windows Defender SmartScreen)
   - macOS requires allowing the app in "Security & Privacy"

## 🔍 Optimization Tips

### Reduce Size
```python
# Exclude more modules in spec file
excludes=[
    'matplotlib', 'scipy', 'pandas', 'numpy.distutils',
    'tkinter', 'unittest', 'email', 'xml', 'http.server',
]
```

### Improve Startup Speed
- Use `--onedir` instead of `--onefile` (default)
- Reduce hidden imports
- Use lazy imports in code

### Code Signing
- Windows: Use SignTool (requires code signing certificate)
- macOS: Use `codesign` (requires Apple Developer account)

## 📚 References

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PySide6 Deployment Guide](https://doc.qt.io/qtforpython-6/deployment.html)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [create-dmg GitHub](https://github.com/create-dmg/create-dmg)

## 🆘 Getting Help

If you encounter packaging issues:
1. Check PyInstaller log files
2. Verify all dependencies are installed
3. Open an issue on the project's GitHub
4. Contact: voicetransor@gmail.com

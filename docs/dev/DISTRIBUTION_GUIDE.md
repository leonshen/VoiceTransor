# Distribution Guide for Developers

This guide explains how to build and distribute VoiceTransor to end users.

## Table of Contents

1. [Overview](#overview)
2. [Build Process](#build-process)
3. [Package Distribution](#package-distribution)
4. [Create Installer (Optional)](#create-installer-optional)
5. [Distribution Channels](#distribution-channels)
6. [Version Management](#version-management)

## Overview

### Distribution Strategy

VoiceTransor uses a **single CUDA-enabled build** that works for all users:
- ✅ **One build for everyone** - includes CUDA 12.1 support
- ✅ Automatically detects and uses NVIDIA GPU (CUDA) if available
- ✅ Gracefully falls back to CPU if no compatible GPU is found
- ✅ No need to maintain separate CPU/GPU builds
- ✅ Similar to Ollama's approach - universal compatibility

**Why single build?**
- Simpler for users (no confusion about which version to download)
- Easier maintenance (one codebase, one build pipeline)
- PyTorch CUDA builds work perfectly fine on CPU-only systems
- Modern disk space (4GB) is acceptable trade-off for better UX

**Alternative not recommended:** Creating separate CPU/GPU builds would require:
- Separate Python environments with different PyTorch versions
- Two build processes to maintain
- Two installer configurations
- User confusion ("Do I have a GPU? Which driver version?")
- Higher support burden

### Package Contents

The distribution package includes:
- Built application (~4GB with CUDA support)
- User documentation (English + Chinese)
- Helper scripts (Ollama installation, etc.)
- Quick start guides

**NOT included (users install separately):**
- FFmpeg (required - users must install)
- Ollama (optional - for AI text processing)
- Whisper models (downloaded automatically on first use)

## Build Process

### Prerequisites

1. **Development Environment:**
   - Python 3.10+
   - All dependencies installed: `pip install -r requirements.txt`
   - PyInstaller: `pip install pyinstaller`

2. **PyTorch with CUDA:**
   ```bash
   pip install torch==2.3.0+cu121 torchaudio==2.3.0+cu121 \
       --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Assets:**
   - Icon file: `assets/icon.ico` (Windows)
   - Icon file: `assets/icon.png` (other platforms)

4. **Optional (for installer):**
   - Inno Setup 6.0+ for Windows installer
   - 7-Zip for creating ZIP archives

### Quick Build - Complete Pipeline (Recommended)

For a complete build including application, distribution package, and installer:

**Windows:**
```bash
scripts\build_all.bat
```

This single command will:
1. ✅ Build the executable with PyInstaller
2. ✅ Create distribution package
3. ✅ Generate ZIP archive (optional)
4. ✅ Create Windows installer with Inno Setup

**Time:** ~10-15 minutes

**Output:**
- `dist\VoiceTransor\VoiceTransor.exe`
- `dist\VoiceTransor-v0.9.0-Windows-x64\`
- `dist\VoiceTransor-v0.9.0-Windows-x64.zip`
- `dist\installer_output\VoiceTransor-v0.9.0-Windows-x64-Setup.exe`

### Manual Build - Individual Steps

If you need more control or troubleshooting:

#### Step 1: Build the Application

```bash
# Clean previous builds
rmdir /s /q build dist  # Windows
# rm -rf build dist      # macOS/Linux

# Build using spec file
pyinstaller VoiceTransor.spec
```

**Build time:** 5-10 minutes

**Output:**
- Windows: `dist\VoiceTransor\VoiceTransor.exe` + dependencies in `_internal\`
- Total size: ~4GB

### Step 2: Test the Build

**Critical tests:**

1. **Launch test:**
   ```bash
   dist\VoiceTransor\VoiceTransor.exe
   ```

2. **GPU detection test:**
   - Check if CUDA is detected (if you have NVIDIA GPU)
   - Verify graceful fallback to CPU (if no GPU)

3. **Import audio test:**
   - Import a sample audio file
   - Verify FFmpeg detection works

4. **Transcription test:**
   - Run a small transcription
   - Verify model download works
   - Check output quality

5. **Ollama integration test (if installed):**
   - Try text operations
   - Verify API communication works

## Package Distribution

### Automated Packaging

Use the provided script from project root:

```bash
scripts\build\package_distribution.bat
```

This script:
1. ✅ Copies built application
2. ✅ Includes all documentation
3. ✅ Creates quick start guides
4. ✅ Generates version info
5. ✅ (Optional) Creates ZIP archive

### Manual Packaging

If you need custom packaging:

```bash
# Create distribution folder in dist/
mkdir dist\VoiceTransor-v0.9.0-Windows-x64

# Copy application
xcopy dist\VoiceTransor dist\VoiceTransor-v0.9.0-Windows-x64\VoiceTransor /E /I /H

# Copy documentation
copy README.md dist\VoiceTransor-v0.9.0-Windows-x64\
copy docs\zh-CN\README.md dist\VoiceTransor-v0.9.0-Windows-x64\README_zh_CN.md
copy docs\INSTALLATION.md dist\VoiceTransor-v0.9.0-Windows-x64\
copy docs\zh-CN\INSTALLATION.md dist\VoiceTransor-v0.9.0-Windows-x64\INSTALLATION_zh_CN.md
copy docs\USER_GUIDE.md dist\VoiceTransor-v0.9.0-Windows-x64\

# Copy helper scripts
copy scripts\setup\install_ollama.bat dist\VoiceTransor-v0.9.0-Windows-x64\

# Create ZIP (requires 7-Zip)
7z a -tzip dist\VoiceTransor-v0.9.0-Windows-x64.zip dist\VoiceTransor-v0.9.0-Windows-x64\*
```

### Distribution Package Structure

```
VoiceTransor-v0.9.0-Windows-x64/
├── VoiceTransor/                 # Application folder
│   ├── VoiceTransor.exe          # Main executable (25MB)
│   └── _internal/                # Dependencies (~4GB)
├── README.md                     # English quick start
├── README_zh_CN.md               # Chinese quick start
├── INSTALLATION.md               # English installation guide
├── INSTALLATION_zh_CN.md         # Chinese installation guide
├── USER_GUIDE.md                 # Detailed user manual
├── QUICK_START.txt               # Simple text guide
├── QUICK_START_zh_CN.txt         # Chinese simple guide
├── VERSION.txt                   # Version and build info
└── install_ollama.bat            # Ollama helper script
```

## Create Installer (Optional)

### Using Inno Setup

1. **Install Inno Setup:**
   - Download from: https://jrsoftware.org/isinfo.php
   - Version 6.0 or later required

2. **Build installer:**
   ```bash
   # From project root
   iscc installer\installer.iss
   ```

3. **Output:**
   - `dist\installer_output\VoiceTransor-v0.9.0-Windows-x64-Setup.exe`
   - Size: ~300-500MB (compressed)

### Installer Features

The generated installer:
- ✅ Installs to Program Files
- ✅ Creates Start Menu shortcuts
- ✅ Creates Desktop icon (optional)
- ✅ Warns about FFmpeg requirement
- ✅ Provides Ollama information
- ✅ Includes uninstaller
- ✅ Supports silent installation

### Signing the Installer (Recommended)

For production releases, sign your installer:

```bash
# Requires code signing certificate
signtool sign /f your-certificate.pfx /p password /t http://timestamp.digicert.com VoiceTransor-v0.9.0-Windows-x64-Setup.exe
```

Benefits:
- No SmartScreen warnings
- Builds trust with users
- Professional appearance

## Distribution Channels

### 1. Direct Download (GitHub Releases)

**Recommended for open source projects:**

```bash
# Create release on GitHub
gh release create v0.9.0 \
  --title "VoiceTransor v0.9.0" \
  --notes "Initial release" \
  VoiceTransor-v0.9.0-Windows-x64.zip \
  VoiceTransor-v0.9.0-Windows-x64-Setup.exe
```

**Release notes template:**

```markdown
## VoiceTransor v0.9.0

### New Features
- AI-powered speech-to-text using Whisper
- Automatic GPU/CPU detection
- Ollama integration for text processing
- Multi-language support (100 languages)

### Download
- **ZIP Package**: VoiceTransor-v0.9.0-Windows-x64.zip (4GB)
- **Installer**: VoiceTransor-v0.9.0-Windows-x64-Setup.exe (450MB)

### System Requirements
- Windows 10 or later
- 8GB RAM minimum
- FFmpeg (install separately)

### Optional
- NVIDIA GPU (GTX 900+) for acceleration
- Ollama for AI text features

### Documentation
- [Installation Guide](INSTALLATION.md)
- [User Guide](USER_GUIDE.md)

### Support
Email: voicetransor@gmail.com
```

### 2. Cloud Storage

For large files:

- **Google Drive**: Share link
- **OneDrive**: Public link
- **Dropbox**: Shared folder
- **AWS S3**: Public bucket

### 3. Website Download

Host on your own website:

```html
<a href="VoiceTransor-v0.9.0-Windows-x64-Setup.exe" download>
  Download VoiceTransor v0.9.0 for Windows x64 (450MB)
</a>
```

## Version Management

### Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

Examples:
- `1.0.0` - Initial release
- `1.0.1` - Bug fix
- `1.1.0` - New features
- `2.0.0` - Breaking changes

### Update Process

1. **Update version in code:**
   - `app/_version.py`: Update `__version__`

2. **Update documentation:**
   - README.md
   - BUILD_INSTRUCTIONS.md
   - CHANGELOG.md (create if needed)

3. **Update build scripts:**
   - `package_distribution.bat`: Update folder name
   - `installer.iss`: Update `#define MyAppVersion`

4. **Rebuild:**
   ```bash
   scripts\build\build_app.bat
   scripts\build\package_distribution.bat
   ```

5. **Test thoroughly:**
   - Clean Windows VM
   - Fresh install
   - All features

6. **Release:**
   - Tag in git: `git tag v0.9.0.0`
   - Push: `git push --tags`
   - Create GitHub release

## Checklist for Release

Before releasing a new version:

- [ ] Code is tested and stable
- [ ] Version number updated in all files
- [ ] CHANGELOG.md updated
- [ ] Clean build completed
- [ ] All features tested
- [ ] Documentation reviewed
- [ ] Package created and tested
- [ ] Installer created (if using)
- [ ] Installer tested on clean machine
- [ ] FFmpeg instructions clear
- [ ] Ollama setup instructions clear
- [ ] Support email working
- [ ] Release notes prepared
- [ ] Git tagged
- [ ] Files uploaded to distribution channel

## Troubleshooting

### Build Issues

**"Module not found" errors:**
- Check all dependencies installed
- Verify spec file includes all hidden imports

**Size too large:**
- Review excludes in spec file
- Consider excluding unused libraries

**Application won't start:**
- Test on clean Windows installation
- Check for missing DLLs
- Review PyInstaller warnings

### Distribution Issues

**Users report "ffprobe not found":**
- Emphasize FFmpeg requirement in all docs
- Consider bundling FFmpeg (increases size by ~100MB)

**GPU not detected:**
- Normal if user has no NVIDIA GPU
- Verify app falls back to CPU gracefully

**Slow startup:**
- Normal for `--onedir` mode
- First-time startup may download models

## Support

For distribution and packaging questions:
- Email: voicetransor@gmail.com
- GitHub Issues: [Your Repo URL]

---

Last updated: 2025-11-02

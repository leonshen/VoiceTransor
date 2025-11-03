# Installation Guide

This guide will help you install and set up VoiceTransor on your system.

[中文安装指南 (Chinese Installation Guide)](./INSTALLATION_zh_CN.md)

## Table of Contents

1. [Download](#download)
2. [System Requirements](#system-requirements)
3. [Install VoiceTransor](#install-voicetransor)
4. [Install FFmpeg (Required)](#install-ffmpeg-required)
5. [Install Ollama (Optional)](#install-ollama-optional)
6. [Verify Installation](#verify-installation)
7. [Troubleshooting](#troubleshooting)

## Download

Download the latest release for your platform:

**Windows:**
- `VoiceTransor-v0.9.0-Windows-x64.zip` (~4GB) - **Universal build for all systems**
- **OR** `VoiceTransor-v0.9.0-Windows-x64-Setup.exe` (~450MB) - Installer version

### 💡 Important: Single Universal Build

VoiceTransor uses a **single build that works for everyone**:
- ✅ **Have NVIDIA GPU?** Automatically uses CUDA acceleration
- ✅ **No GPU?** Automatically uses CPU (works perfectly, just slower)
- ✅ **No need to choose** between CPU/GPU versions
- ✅ **Same installer** works on all Windows 10+ systems

This is similar to how Ollama works - one download, automatic hardware detection.

## System Requirements

### Minimum Requirements

- **Operating System:**
  - Windows 10 or later (64-bit)
  - macOS 10.15 (Catalina) or later
  - Linux (Ubuntu 20.04+, Debian 11+, or equivalent)

- **Hardware:**
  - 8GB RAM
  - 5GB free disk space (for application and models)
  - Dual-core processor

### Recommended Requirements

- **Hardware:**
  - 16GB RAM
  - 10GB free disk space
  - Quad-core processor or better

### For GPU Acceleration (Optional)

- **NVIDIA GPU:**
  - GTX 900 series or newer (GTX 1050, RTX 20/30/40 series, etc.)
  - 4GB+ VRAM
  - Driver version >= 525.60.13

- **Apple Silicon:**
  - M1, M2, or M3 chip
  - Automatically detected and used

**Note:** GPU acceleration is optional. The application works perfectly fine on CPU, just slower.

## Install VoiceTransor

### Windows

1. **Extract the archive:**
   - Right-click `VoiceTransor-Windows.zip`
   - Select "Extract All..."
   - Choose a destination folder (e.g., `C:\Program Files\VoiceTransor`)

2. **Launch the application:**
   - Navigate to the extracted folder
   - Double-click `VoiceTransor.exe`

3. **Windows Security Warning:**
   - If you see "Windows protected your PC", click "More info"
   - Then click "Run anyway"
   - This is normal for unsigned applications

### macOS

1. **Extract the archive:**
   - Double-click `VoiceTransor-macOS.zip`
   - Move `VoiceTransor.app` to Applications folder

2. **First launch:**
   - Right-click `VoiceTransor.app` and select "Open"
   - Click "Open" in the security dialog

3. **Grant permissions:**
   - Allow access to files when prompted

### Linux

1. **Extract the archive:**
   ```bash
   unzip VoiceTransor-Linux.zip -d ~/Applications/VoiceTransor
   cd ~/Applications/VoiceTransor
   ```

2. **Make executable:**
   ```bash
   chmod +x VoiceTransor
   ```

3. **Launch:**
   ```bash
   ./VoiceTransor
   ```

## Install FFmpeg (Required)

VoiceTransor requires FFmpeg to process audio files. You must install it separately.

### Windows

**Option 1: Automatic (Recommended)**

1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/
2. Download **"ffmpeg-release-essentials.zip"**
3. Extract to `C:\ffmpeg`
4. Add to PATH:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Go to "Advanced" tab
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New"
   - Add: `C:\ffmpeg\bin`
   - Click "OK" on all windows
5. **Restart your computer** (or at least log out and back in)

**Option 2: Using Package Manager**

If you have Chocolatey:
```bash
choco install ffmpeg
```

If you have Scoop:
```bash
scoop install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

### macOS

**Using Homebrew (Recommended):**
```bash
brew install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

### Linux

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

## Install Ollama (Optional)

Ollama enables AI-powered text processing (summarize, translate, extract key points, etc.). This is optional but recommended.

### What is Ollama?

- Local AI models (no cloud, your data stays private)
- Works on both CPU and GPU
- Required for text processing features in VoiceTransor

### Installation

**Windows:**

1. Download installer from: https://ollama.com/download
2. Run the installer
3. Open Command Prompt and verify:
   ```bash
   ollama --version
   ```

**macOS:**

1. Download from: https://ollama.com/download
2. Install the .dmg file
3. Verify in Terminal:
   ```bash
   ollama --version
   ```

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Download a Model

After installing Ollama:

1. **Start Ollama service** (if not auto-started):
   ```bash
   ollama serve
   ```

2. **Pull a model** (in a new terminal):
   ```bash
   # For English
   ollama pull llama3.1:8b

   # For Chinese/English
   ollama pull qwen2.5:7b
   ```

3. **Model sizes:**
   - `llama3.1:8b` - ~4.7GB
   - `qwen2.5:7b` - ~4.4GB

**Note:** Models are downloaded to:
- Windows: `%USERPROFILE%\.ollama\models`
- macOS/Linux: `~/.ollama/models`

## Verify Installation

### Test VoiceTransor

1. Launch VoiceTransor
2. Try importing a small audio file
3. If FFmpeg is working, you should see audio information

### Test GPU Detection (if you have NVIDIA GPU)

1. Go to transcription settings
2. Select Device: "auto" or "cuda"
3. Start a transcription
4. Check the logs - should mention using CUDA

If GPU is not detected, the app will automatically use CPU.

### Test Ollama (if installed)

1. In VoiceTransor, try "Run Text Operation"
2. Select a preset (e.g., "Summarize")
3. If Ollama is running and has a model, it should work

## Troubleshooting

### "ffprobe not found" Error

**Cause:** FFmpeg is not installed or not in PATH.

**Solution:**
1. Verify FFmpeg is installed: `ffmpeg -version`
2. If not found, reinstall FFmpeg
3. Make sure FFmpeg is in your PATH
4. Restart VoiceTransor (or your computer)

### "Ollama is not running" Error

**Cause:** Ollama service is not started.

**Solution:**
1. Open a terminal
2. Run: `ollama serve`
3. Keep this terminal open
4. Try again in VoiceTransor

**Auto-start Ollama (Optional):**
- Windows: Create a scheduled task
- macOS: Add to Login Items
- Linux: Enable systemd service

### Application Won't Start

**Windows:**
- Try running as Administrator
- Check Windows Defender hasn't blocked it

**macOS:**
- Go to System Preferences → Security & Privacy
- Click "Open Anyway"

**Linux:**
- Check file permissions: `chmod +x VoiceTransor`
- Install required libraries: `sudo apt install libxcb-cursor0`

### GPU Not Detected

**Check your GPU:**
```bash
# NVIDIA
nvidia-smi
```

**Update drivers:**
- NVIDIA: Download from https://www.nvidia.com/drivers
- Minimum version: 525.60.13 for CUDA 12.1

**Don't worry if GPU doesn't work:**
- The app will automatically use CPU
- Everything will still work, just slower

## Next Steps

Once installation is complete:

1. Read the [User Guide](./USER_GUIDE.md) for detailed usage instructions
2. Try your first transcription
3. Explore AI text processing with Ollama

## Getting Help

If you encounter issues not covered here:

1. Check [USER_GUIDE.md - Troubleshooting](./USER_GUIDE.md#troubleshooting)
2. Email: voicetransor@gmail.com

---

Happy transcribing! 🎉

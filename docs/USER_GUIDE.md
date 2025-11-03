# VoiceTransor User Guide

Welcome to **VoiceTransor**! This guide will help you get started with the application.

## 🎯 What is VoiceTransor?

VoiceTransor is a speech-to-text application that:

- Converts audio files to text using AI (Whisper)
- Processes text with AI assistance (summarize, translate, etc.)
- Exports results as TXT or PDF files
- Works completely offline (your data stays on your computer)

## 📋 Before You Start

### Required: FFmpeg

VoiceTransor needs **FFmpeg** to process audio files.

#### Windows

**Option 1: Automatic (Recommended)**

1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Choose "ffmpeg-release-essentials.zip"
3. Extract to `C:\ffmpeg`
4. Add to PATH:
   - Open "Environment Variables" (search in Start menu)
   - Under "System variables", find "Path"
   - Click "Edit" → "New"
   - Add: `C:\ffmpeg\bin`
   - Click "OK" on all windows
5. Restart VoiceTransor

**Option 2: Package Manager**

```bash
# Using Chocolatey
choco install ffmpeg

# Using Scoop
scoop install ffmpeg
```

#### macOS

```bash
# Using Homebrew (recommended)
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Optional: Ollama (for Text Operations)

Ollama enables AI-powered text processing (summarize, translate, etc.) **without sending data to the cloud**.

#### Installation

**Windows:**

- Run `install_ollama.bat` (included with VoiceTransor)
- Or download from: https://ollama.com/download

**macOS:**

```bash
# Download from: https://ollama.com/download
# Or use Homebrew
brew install ollama
```

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Setup

1. Start Ollama service:

   ```bash
   ollama serve
   ```

2. Download a model (first time only):

   ```bash
   # For English
   ollama pull llama3.1:8b

   # For Chinese/English
   ollama pull qwen2.5:7b
   ```

3. Models are ~4-5GB each and stored in:
   - Windows: `%USERPROFILE%\.ollama\models`
   - macOS/Linux: `~/.ollama/models`

## 🚀 Getting Started

### First Launch

1. **Launch VoiceTransor**

2. **Check FFmpeg** (first time)

   - Try importing an audio file
   - If you see "ffprobe not found", install FFmpeg (see above)

3. **Import Audio**

   - Click "Import Audio"
   - Supported formats: WAV, MP3, M4A, FLAC, OGG, AAC

4. **Transcribe**

   - Click "Transcribe to Text"
   - Choose settings:
     - **Model**: `tiny` (fast) → `base` (balanced) → `small` (accurate)
     - **Device**:
       - `auto` - Let the app choose
       - `cuda` - NVIDIA GPU (fastest)
       - `mps` - Apple Silicon GPU
       - `cpu` - Works on any computer (slower)
     - **Language**: Auto-detect or select specific language

5. **Wait for Transcription**

   - First time downloads the model (~140MB - ~960MB)
   - Progress bar shows ETA
   - Can resume if interrupted

6. **Save or Process**
   - Save as TXT
   - Or use "Run Text Operation" with Ollama

## 💡 Tips & Tricks

### For Best Results

1. **Audio Quality**

   - Clear audio = better transcription
   - Reduce background noise
   - Use good microphone

2. **Model Selection**

   - `tiny`: Fast, good for clear speech
   - `base`: Best balance (recommended)
   - `small`: Most accurate, slower

3. **Device Selection**
   - GPU is 10-50x faster than CPU
   - First transcription is slower (model loading)
   - Subsequent ones are faster

### Text Operations (with Ollama)

1. **Summarize**

   - Select "Summarize" preset
   - Or write custom prompt

2. **Translate**

   - Select "Translate to Chinese" preset
   - Or specify target language

3. **Custom Operations**
   - Write what you want in the Prompt panel
   - Examples:
     - "Extract action items from this meeting"
     - "Create a blog post from this transcript"
     - "Fix grammar and spelling errors"

### Keyboard Shortcuts

- `Ctrl/Cmd + +/-`: Zoom in/out
- `Ctrl/Cmd + 0`: Reset zoom

### Language Switching

- Go to **View** → **Language**
- Available: English, 简体中文
- Changes apply immediately

## 🔧 Troubleshooting

### "ffprobe not found" Error

**Cause:** FFmpeg is not installed or not in PATH

**Solution:**

1. Install FFmpeg (see "Before You Start" section)
2. Make sure to add FFmpeg to PATH
3. Restart VoiceTransor
4. Test: Open terminal and run `ffmpeg -version`

### "Ollama is not running" Error

**Cause:** Ollama service is not started

**Solution:**

1. Open terminal/command prompt
2. Run: `ollama serve`
3. Keep terminal open
4. Try text operation again

**Alternative:** Set Ollama to start automatically:

- Windows: Create scheduled task
- macOS: Add to login items
- Linux: Use systemd service

### Transcription is Very Slow

**Possible causes:**

1. Using CPU instead of GPU
   - Solution: Select `cuda` or `mps` device
2. Large audio file
   - Solution: Split into smaller files
3. Computer resources busy
   - Solution: Close other applications

### Model Download Fails

**Cause:** Network issues or insufficient disk space

**Solution:**

1. Check internet connection
2. Ensure 5GB+ free disk space
3. Check firewall settings
4. Try again later

### Application Won't Start

**Windows:**

- Right-click → "Run as Administrator"
- Allow in Windows Defender

**macOS:**

- Go to System Preferences → Security & Privacy
- Click "Open Anyway"

### Text is Garbled or Incorrect

**Possible causes:**

1. Wrong language selected
   - Solution: Use "Auto" or select correct language
2. Poor audio quality
   - Solution: Use clearer audio
3. Wrong model size
   - Solution: Try larger model (`small` instead of `tiny`)

## 📊 System Requirements

### Minimum

- **OS:** Windows 10 / macOS 10.15 / Linux
- **RAM:** 4GB
- **Disk:** 2GB free space
- **Processor:** Any modern CPU

### Recommended

- **RAM:** 8GB+ (16GB for Ollama)
- **GPU:** NVIDIA GPU with 4GB+ VRAM or Apple Silicon
- **Disk:** 10GB free space (for models)

## 🆘 Getting Help

If you encounter issues:

1. **Check this guide** - Most common issues are covered
2. **Check logs** - Look for error messages in the app
3. **GitHub Issues** - https://github.com/leonshen/VoiceTransor/issues
4. **Email Support** - voicetransor@gmail.com

## 📚 More Information

- **Whisper Models:** https://github.com/openai/whisper
- **Ollama:** https://ollama.com
- **FFmpeg:** https://ffmpeg.org

---

Thank you for using VoiceTransor! 🎉

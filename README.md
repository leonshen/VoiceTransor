# VoiceTransor

[![Release](https://img.shields.io/github/v/release/leonshen/VoiceTransor?include_prereleases)](https://github.com/leonshen/VoiceTransor/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/leonshen/VoiceTransor)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

**AI-Powered Speech-to-Text with Local Processing**

VoiceTransor is a desktop application that converts audio to text using OpenAI's Whisper model, with optional AI text processing powered by Ollama. Everything runs locally on your computer - your data never leaves your machine.

[中文版说明 (Chinese README)](./docs/zh-CN/README.md) | [Developer Guide](./docs/dev/README_DEV.md)

## Features

- **Accurate Speech Recognition** - Powered by OpenAI Whisper
- **GPU Acceleration** - Automatic CUDA/MPS detection for faster processing
- **AI Text Processing** - Summarize, translate, or process transcripts with Ollama
- **Multiple Export Formats** - Save as TXT or PDF
- **Privacy First** - All processing happens locally
- **Cross-Platform** - Windows, macOS, and Linux support
- **Multiple Languages** - Supports 100 languages

## Quick Start

### 1. System Requirements

**Minimum:**
- Windows 10 / macOS 10.15 / Linux
- 8GB RAM
- 5GB free disk space

**Recommended for GPU Acceleration:**
- NVIDIA GPU (GTX 900 series or newer)
- Driver version >= 525.60 (for CUDA support)

**Note:** GPU is optional - the app automatically detects your hardware and falls back to CPU if needed.

### 2. Installation

**Windows:**
1. Download `VoiceTransor-v0.9.0-Windows-x64-Setup.exe` from [Releases](https://github.com/leonshen/VoiceTransor/releases)
2. Run the installer and follow the setup wizard
3. Launch VoiceTransor from the Start Menu or Desktop shortcut

**macOS / Linux:**
- *Coming soon* - Currently only Windows installer is available
- For development setup, see [Developer Guide](./docs/dev/README_DEV.md)

**Important:** You also need to install FFmpeg (see below).

### 3. Install FFmpeg (Required)

VoiceTransor needs FFmpeg for audio processing.

**Windows:**
- Download: https://www.gyan.dev/ffmpeg/builds/
- Choose "ffmpeg-release-essentials.zip"
- Extract and add to PATH ([How?](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/))

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
```

### 4. First Use

1. Launch VoiceTransor
2. Click "Import Audio" (supports WAV, MP3, M4A, FLAC, etc.)
3. Click "Transcribe to Text"
4. Choose settings:
   - **Model**: `base` (recommended for most users)
   - **Device**: `auto` (automatically uses GPU if available)
   - **Language**: Auto-detect or select specific language
5. Wait for transcription (first time downloads the model ~140MB)
6. Export as TXT or process with AI

## Optional: Install Ollama

Ollama enables AI-powered text processing (summarize, translate, etc.) - completely offline.

**Installation:**
1. Download from: https://ollama.com/download
2. Install and run `ollama serve`
3. Pull a model:
   ```bash
   ollama pull llama3.1:8b  # English
   ollama pull qwen2.5:7b   # Chinese/English
   ```

**Note:** Ollama works on both CPU and GPU - no special setup needed.

## Performance

**Transcription Speed (1 hour audio):**

| Hardware | Time |
|----------|------|
| CPU (8-core) | ~30-60 min |
| NVIDIA RTX 3060 | ~2-5 min |
| Apple M1 Pro | ~3-6 min |

**GPU Compatibility:**
- ✅ **Single universal build** - works on both GPU and CPU systems
- ✅ Automatic detection - no manual configuration needed
- ✅ NVIDIA GPUs (GTX 900+, RTX series) - uses CUDA acceleration
- ✅ Apple Silicon (M1/M2/M3) - uses Metal Performance Shaders
- ✅ Graceful fallback to CPU if GPU unavailable
- ℹ️ **No separate CPU/GPU versions** - one installer works for everyone

## Documentation

- [User Guide](./docs/USER_GUIDE.md) - Detailed usage instructions
- [Installation Guide](./docs/INSTALLATION.md) - Step-by-step installation
- [Build Instructions](./docs/dev/BUILD_INSTRUCTIONS.md) - For developers
- [中文文档](./docs/zh-CN/) - Chinese documentation

## Troubleshooting

**"ffprobe not found"**
- Install FFmpeg and ensure it's in your PATH

**Slow transcription**
- Use smaller model (`tiny` or `base`)
- Check Device setting is `auto` or `cuda`
- Ensure GPU drivers are up to date

**"Ollama is not running"**
- Open terminal and run `ollama serve`

For more help, see [USER_GUIDE.md](./docs/USER_GUIDE.md#troubleshooting)

## License

MIT License. See [LICENSE](LICENSE) for details.

## Support

- GitHub Issues: https://github.com/leonshen/VoiceTransor/issues
- Email: voicetransor@gmail.com

---

Made with ❤️ using [OpenAI Whisper](https://github.com/openai/whisper) and [Ollama](https://ollama.com)

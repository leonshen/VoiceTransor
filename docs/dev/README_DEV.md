# VoiceTransor

**VoiceTransor** is an open-source speech-to-text and text assistant.  
It provides a simple workflow to transcribe audio locally using Whisper, process text with AI, and export results in multiple formats.

---

## ✨ Features

- Import audio files
- Local transcription with Whisper (supports resume from interruption)
- AI-powered text processing
- Export results as TXT / PDF
- Cross-platform: Windows, macOS

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- FFmpeg installed and available in PATH
- Virtual environment (recommended)

### Configure AI Text Processing

VoiceTransor uses **Ollama** for local AI-powered text processing. This keeps your data completely private without sending it to the cloud.

**Quick Setup:**

1. **Windows:** Run `scripts\setup\install_ollama.bat` from project root (automatic installation)
2. **Manual installation:** Download from [ollama.com/download](https://ollama.com/download)
3. **Start service:** Run `ollama serve` in a terminal
4. **Download a model:** Run `ollama pull llama3.1:8b`

For detailed setup instructions, see [OLLAMA_SETUP_GUIDE.md](../OLLAMA_SETUP_GUIDE.md) ([中文版](../OLLAMA_SETUP_GUIDE_CN.md)).

**Recommended Models:**
- `llama3.1:8b` - English (default, ~4.7GB)
- `qwen2.5:7b` - Balanced Chinese/English (~4.4GB)
- `gemma2:9b` - High quality (~5.4GB)

**System Requirements:**
- **GPU mode:** NVIDIA GPU with 8GB+ VRAM (recommended)
- **CPU mode:** 16GB+ RAM (slower but works)

### Setup

```bash
git clone https://github.com/leonshen/VoiceTransor.git
cd VoiceTransor
pip install -r requirements.txt
```

### Windows GPU (CUDA) setup

If you want Whisper to use an NVIDIA GPU on Windows:

1. Uninstall any existing CPU-only PyTorch wheels inside your virtualenv:
   ```bash
   pip uninstall torch torchvision torchaudio -y
   ```
2. Install the matching CUDA wheels (examples below use CUDA 12.1; pick the build that matches your driver):
   ```bash
   pip install torch==2.3.0+cu121 torchvision==0.18.0+cu121 torchaudio==2.3.0+cu121 \
       --index-url https://download.pytorch.org/whl/cu121
   ```
3. Verify CUDA is detected before launching VoiceTransor:
   ```bash
   python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
   ```
   The command should print `True` and a CUDA version string.

## Run

Make sure the virtual environment is activated

```bash
python -m app.main
```

## 📧 Contact

For support or collaboration: voicetransor@gmail.com

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

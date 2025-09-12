# VoiceTransor

**VoiceTransor** is an open-source speech-to-text and text assistant.  
It provides a simple workflow to transcribe audio locally using Whisper, process text with AI, and export results in multiple formats.

---

## ✨ Features
- Import audio files
- Local transcription with Whisper (supports resume from interruption)
- AI-powered text processing (OpenAI integration)
- Export results as TXT / PDF
- Cross-platform: Windows, macOS 

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- FFmpeg installed and available in PATH
- Virtual environment (recommended)

### Configure OpenAI API
Some features (AI-powered text processing) require an OpenAI API key and a project ID.  

1. Create an account at [OpenAI](https://platform.openai.com/).  
2. Generate an API key from the [API Keys page](https://platform.openai.com/account/api-keys).  
3. At the same time, create a **Project** in your OpenAI account — most API keys now need to be associated with a project.  
4. In VoiceTransor, open **Settings → OpenAI** and enter your **API Key** and **Project ID**.

### Setup
```bash
git clone https://github.com/leonshen/VoiceTransor.git
cd VoiceTransor
pip install -r requirements.txt
```

## Run
Make sure the virtual environment is activated
```bash
python -m app.main
```

## 📧 Contact
For support or collaboration: voicetransor@gmail.com

## 📜 License
MIT License. See [LICENSE](LICENSE) for details.

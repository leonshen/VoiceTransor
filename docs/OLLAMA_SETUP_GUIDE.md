# Ollama Installation and Usage Guide

VoiceTransor uses Ollama to provide local AI text processing, keeping your data completely private without uploading to the cloud.

---

## 📋 System Requirements

### Recommended Configuration (GPU Mode)
- **GPU:** NVIDIA graphics card with 8GB+ VRAM
- **Memory:** 16GB+ RAM
- **Disk:** ~4-8GB per model
- **OS:** Windows 10/11, macOS, Linux

### Minimum Configuration (CPU Mode)
- **CPU:** Modern multi-core processor
- **Memory:** 16GB+ RAM (32GB recommended)
- **Disk:** ~4-8GB per model
- **Note:** CPU mode runs 3-10x slower than GPU

### Model Size Reference
| Model | Size | VRAM Required | Recommended Use |
|-------|------|---------------|----------------|
| llama3.1:8b | ~4.7GB | 6-8GB | English text processing (default) |
| qwen2.5:7b | ~4.4GB | 6-8GB | Balanced Chinese/English |
| gemma2:9b | ~5.4GB | 8-10GB | High-quality text processing |
| llama3.1:70b | ~40GB | 48GB+ | Top quality (requires high-end hardware) |

---

## 🚀 Quick Installation (Windows)

### Method 1: Using Automatic Installation Script (Recommended)

1. Double-click `install_ollama.bat` in the project root directory
2. The script will automatically:
   - Download the Ollama installer
   - Install Ollama
   - Start the Ollama service
   - Optionally download the default model (llama3.1:8b)
3. Wait for installation to complete

### Method 2: Manual Installation

1. **Download Ollama**
   - Visit: https://ollama.com/download
   - Download Windows version (~300MB)

2. **Install Ollama**
   - Run the downloaded installer
   - Follow the installation prompts
   - Ollama will be automatically added to system PATH

3. **Start Ollama Service**
   - Open Command Prompt (CMD) or PowerShell
   - Run: `ollama serve`
   - Keep this window open (or let it run in background)

4. **Download Model**
   - Open another Command Prompt
   - Run: `ollama pull llama3.1:8b`
   - Wait for download to complete (~4.7GB, takes a few minutes)

---

## 🍎 macOS Installation

### Using Homebrew (Recommended)
```bash
brew install ollama
```

### Manual Installation
1. Visit https://ollama.com/download
2. Download macOS version
3. Install and run

### Download Model
```bash
ollama pull llama3.1:8b
```

---

## 🐧 Linux Installation

### One-Line Install Script
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Start Service
```bash
ollama serve &
```

### Download Model
```bash
ollama pull llama3.1:8b
```

---

## ✅ Verify Installation

### Check if Ollama is Installed
```bash
ollama --version
```

### Check if Service is Running
```bash
# Windows
tasklist | findstr ollama

# macOS/Linux
ps aux | grep ollama
```

### List Installed Models
```bash
ollama list
```

### Test Model
```bash
ollama run llama3.1:8b "Hello, how are you?"
```

---

## 🎯 Using in VoiceTransor

### 1. Ensure Ollama Service is Running
VoiceTransor will automatically detect if Ollama is running. If not:
- Windows: Run `ollama serve`
- macOS/Linux: Run `ollama serve &`

### 2. Select Model
In the "Run Text Operations" dialog:
- Choose a model from the dropdown menu, or
- Manually enter a custom model name

### 3. Enter Processing Instruction
Enter what you want the AI to do, for example:
- "Summarize the key points of this text"
- "Translate to English"
- "Extract key information and list as bullet points"
- "Correct grammar errors"

### 4. Wait for Processing
- GPU mode: Usually a few seconds to tens of seconds
- CPU mode: May take 1-5 minutes

---

## 🛠️ Common Commands

### Model Management
```bash
# Download models
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull gemma2:9b

# List installed models
ollama list

# Remove model (free up space)
ollama rm llama3.1:8b

# Show model information
ollama show llama3.1:8b
```

### Service Management
```bash
# Start service
ollama serve

# Stop service (Windows)
taskkill /IM ollama.exe /F

# Stop service (macOS/Linux)
killall ollama
```

---

## 💡 Recommended Model Selection

### 🚀 Quick Recommendations
| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| Primarily English | llama3.1:8b | Fast, high quality, default choice |
| Chinese/English Mix | qwen2.5:7b | Excellent Chinese support |
| High Quality | gemma2:9b | Google-made, high quality |
| Limited Hardware | llama3.1:8b | Lowest resource requirements |

### 🎨 Detailed Comparison

#### llama3.1:8b (Default)
- ✅ Excellent English processing
- ✅ Fast
- ✅ Moderate resource usage (6-8GB VRAM)
- ⚠️ Limited Chinese support
- **Best for:** English text processing, daily use

#### qwen2.5:7b
- ✅ Balanced Chinese/English
- ✅ Strong Chinese comprehension
- ✅ Good cultural adaptation
- **Best for:** Chinese or mixed Chinese/English text

#### gemma2:9b
- ✅ High quality
- ✅ Official Google support
- ⚠️ Slightly higher VRAM requirement (8-10GB)
- **Best for:** High-quality output

---

## 🐛 FAQ

### Q1: Ollama service won't start
**A:**
- Check if Ollama process is already running
- Try restarting your computer
- Check firewall settings
- Ensure port 11434 is not occupied

### Q2: Model download failed or very slow
**A:**
- Check network connection
- Try using VPN or proxy
- Wait and retry later
- Ensure sufficient disk space

### Q3: VoiceTransor shows "Ollama unavailable"
**A:**
1. Confirm Ollama service is running
2. Visit http://localhost:11434 in browser to check
3. Run `ollama list` to confirm models are downloaded
4. Restart VoiceTransor

### Q4: Processing is very slow
**A:**
- **Check GPU:** Ensure CUDA is working properly
- **Try smaller model:** Switch to llama3.1:8b
- **Close other programs:** Free up GPU/memory
- **CPU mode is naturally slow**

### Q5: Out of Memory error
**A:**
- Switch to a smaller model
- Close other GPU programs
- Use CPU mode (set environment variable)
- Upgrade graphics card

### Q6: How to use CPU instead of GPU?
**A:**
Set environment variables:
```bash
# Windows CMD
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_SKIP_CPU_CHECK=1

# Restart ollama serve
```

---

## 📚 More Resources

### Official Documentation
- Ollama Website: https://ollama.com
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama

### Community Resources
- Discord: https://discord.gg/ollama
- Reddit: r/ollama
- Chinese Community: Various AI forums

---

## 🔧 Advanced Configuration

### Modify Ollama Listening Address
```bash
# Allow remote access (use with caution)
set OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

### Specify GPU Device
```bash
# CUDA device selection
set CUDA_VISIBLE_DEVICES=0
ollama serve
```

### Adjust Model Parameters
In code you can modify:
- `temperature`: Controls randomness (0.0-1.0)
- `top_p`: Nucleus sampling parameter
- `max_tokens`: Maximum output length

---

## 📞 Getting Help

If you encounter problems:
1. Check the "FAQ" section in this document
2. Consult Ollama official documentation
3. Ask questions in VoiceTransor GitHub Issues
4. Visit Ollama community for help

---

**Enjoy using VoiceTransor! 🎉**

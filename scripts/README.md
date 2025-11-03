# Scripts Directory

This directory contains various scripts for building, packaging, and setting up VoiceTransor.

## Directory Structure

```
scripts/
├── build/              # Build and packaging scripts
│   ├── build_app.bat           # Build Windows executable
│   ├── build_app.sh            # Build macOS/Linux executable
│   └── package_distribution.bat # Create distribution package
├── setup/              # Setup and installation scripts
│   ├── install_ollama.bat      # Install Ollama on Windows
│   └── install_ollama.sh       # Install Ollama on macOS/Linux
├── build_all.bat       # Complete build pipeline (Windows)
└── run.bat             # Quick run script for development
```

## Usage

### 🚀 Complete Build Pipeline (Recommended)

Build everything in one command:

**Windows:**
```bash
scripts\build_all.bat
```

This will automatically:
1. Build the application executable
2. Create the distribution package (with ZIP option)
3. Generate the Windows installer

**Time:** ~10-15 minutes
**Output:**
- `dist\VoiceTransor\VoiceTransor.exe`
- `dist\VoiceTransor-v0.9.0-Windows-x64\` (distribution folder)
- `dist\VoiceTransor-v0.9.0-Windows-x64.zip` (optional)
- `dist\installer_output\VoiceTransor-v0.9.0-Windows-x64-Setup.exe`

### Individual Build Steps

If you need to run steps separately:

#### Building the Application

**Windows:**
```bash
scripts\build\build_app.bat
```

**macOS/Linux:**
```bash
./scripts/build/build_app.sh
```

#### Creating Distribution Package

**Windows:**
```bash
scripts\build\package_distribution.bat
```

### Installing Ollama

**Windows:**
```bash
scripts\setup\install_ollama.bat
```

**macOS/Linux:**
```bash
./scripts/setup/install_ollama.sh
```

## Quick Development Run

**Windows:**
```bash
scripts\run.bat
```

This runs the application directly from source code without building.

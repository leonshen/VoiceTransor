#!/bin/bash
# Ollama Installation Script for VoiceTransor (macOS/Linux)
# This script helps users install Ollama on macOS and Linux

set -e

echo "========================================"
echo "Ollama Installation for VoiceTransor"
echo "========================================"
echo ""

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "[INFO] Detected OS: $OS"
echo "[INFO] Architecture: $ARCH"
echo ""

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "[OK] Ollama is already installed!"
    echo ""
    ollama --version
    echo ""
    # Skip to service check
    CHECK_SERVICE=1
else
    CHECK_SERVICE=0
    echo "[INFO] Ollama is not installed. Starting installation..."
    echo ""

    case "$OS" in
        Darwin*)
            # macOS installation
            echo "[INFO] Installing Ollama for macOS..."
            echo ""

            # Check if Homebrew is available (optional method)
            if command -v brew &> /dev/null; then
                echo "[OPTION 1] Install via Homebrew (recommended):"
                echo "    brew install ollama"
                echo ""
            fi

            echo "[OPTION 2] Download installer from ollama.com:"
            echo "    https://ollama.com/download"
            echo ""

            # Try to download and run installer
            INSTALLER_URL="https://ollama.com/download/Ollama-darwin.zip"

            read -p "Would you like to download the installer now? (y/N): " -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "[INFO] Downloading Ollama installer..."
                TEMP_DIR=$(mktemp -d)
                curl -L "$INSTALLER_URL" -o "$TEMP_DIR/Ollama.zip"

                if [ -f "$TEMP_DIR/Ollama.zip" ]; then
                    echo "[OK] Download completed!"
                    echo "[INFO] Extracting installer..."
                    unzip -q "$TEMP_DIR/Ollama.zip" -d "$TEMP_DIR"

                    echo ""
                    echo "[INFO] Please drag Ollama.app to your Applications folder"
                    open "$TEMP_DIR"

                    # Clean up will happen on next system reboot
                else
                    echo "[ERROR] Failed to download installer."
                    echo "Please visit https://ollama.com/download to install manually."
                    exit 1
                fi
            else
                echo "[INFO] Please install Ollama manually from: https://ollama.com/download"
                exit 0
            fi
            ;;

        Linux*)
            # Linux installation
            echo "[INFO] Installing Ollama for Linux..."
            echo ""
            echo "Running official installation script..."
            echo ""

            curl -fsSL https://ollama.com/install.sh | sh

            if command -v ollama &> /dev/null; then
                echo ""
                echo "[OK] Ollama has been installed successfully!"
                echo ""
                ollama --version
            else
                echo ""
                echo "[ERROR] Installation failed."
                echo "Please visit https://ollama.com/download for manual installation."
                exit 1
            fi
            ;;

        *)
            echo "[ERROR] Unsupported operating system: $OS"
            echo "Please visit https://ollama.com/download for manual installation."
            exit 1
            ;;
    esac
fi

# Check and start Ollama service
echo ""
echo "========================================"
echo "Checking Ollama Service"
echo "========================================"
echo ""

# Check if Ollama is running
if pgrep -x "ollama" > /dev/null; then
    echo "[OK] Ollama service is already running!"
    echo ""
else
    echo "[INFO] Starting Ollama service..."
    echo ""

    case "$OS" in
        Darwin*)
            # macOS: Start via 'ollama serve' in background
            nohup ollama serve > /dev/null 2>&1 &
            sleep 3
            echo "[OK] Ollama service started in background."
            ;;
        Linux*)
            # Linux: Use systemd if available
            if command -v systemctl &> /dev/null; then
                sudo systemctl start ollama 2>/dev/null || {
                    nohup ollama serve > /dev/null 2>&1 &
                    sleep 3
                }
                echo "[OK] Ollama service started."
            else
                nohup ollama serve > /dev/null 2>&1 &
                sleep 3
                echo "[OK] Ollama service started in background."
            fi
            ;;
    esac
    echo ""
fi

# Pull recommended model
echo "========================================"
echo "Downloading Recommended Model"
echo "========================================"
echo ""
echo "Recommended model: llama3.1:8b"
echo "  - Size: ~4.7GB"
echo "  - RAM: 8GB recommended"
echo "  - Good balance of speed and quality"
echo ""

read -p "Download llama3.1:8b now? (Y/n): " -n 1 -r
echo ""
PULL_MODEL="${REPLY:-Y}"

if [[ $PULL_MODEL =~ ^[Yy]$ ]]; then
    echo ""
    echo "[INFO] Downloading llama3.1:8b..."
    echo "This may take several minutes depending on your internet speed."
    echo ""

    ollama pull llama3.1:8b

    if [ $? -eq 0 ]; then
        echo ""
        echo "[OK] Model llama3.1:8b downloaded successfully!"
    else
        echo ""
        echo "[WARNING] Failed to download model. You can try again later:"
        echo "    ollama pull llama3.1:8b"
    fi
else
    echo ""
    echo "[INFO] Skipping model download."
    echo "You can download models later with:"
    echo "    ollama pull llama3.1:8b"
    echo "    ollama pull qwen2.5:7b"
    echo "    ollama pull gemma2:9b"
fi

echo ""
echo "========================================"
echo "Installation Summary"
echo "========================================"
echo ""

# List installed models
echo "Installed models:"
ollama list 2>/dev/null || echo "  (No models installed yet)"

echo ""
echo "========================================"
echo "Next Steps"
echo "========================================"
echo ""
echo "1. Ollama is now ready to use!"
echo "2. Make sure Ollama service is running"
echo "3. Open VoiceTransor and try 'Run Text Operations'"
echo ""
echo "Useful commands:"
echo "  ollama serve          - Start Ollama service"
echo "  ollama list           - List installed models"
echo "  ollama pull [model]   - Download a model"
echo "  ollama rm [model]     - Remove a model"
echo ""
echo "For more information, visit: https://ollama.com"
echo ""
echo "========================================"
echo ""

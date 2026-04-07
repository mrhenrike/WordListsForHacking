#!/usr/bin/env bash
# setup_venv.sh — Setup virtual environment for wfh.py
# Author: André Henrique (@mrhenrike)
# Compatible with Linux, macOS, and Android (Termux)

set -e

VENV_DIR=".venv"
PYTHON_MIN="3.8"

echo "=== wfh.py — Virtual Environment Setup ==="
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)
        if [ -d "/data/data/com.termux" ]; then
            PLATFORM="android-termux"
        else
            PLATFORM="linux"
        fi
        ;;
    Darwin*)  PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *)        PLATFORM="unknown" ;;
esac
echo "Platform detected: $PLATFORM"

# Install OS-level prerequisites
install_prereqs() {
    echo ""
    echo "--- Installing OS prerequisites ---"
    case "$PLATFORM" in
        linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y -qq python3 python3-pip python3-venv \
                    libxml2-dev libxslt1-dev zlib1g-dev \
                    tesseract-ocr libtesseract-dev 2>/dev/null || true
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-pip python3-devel \
                    libxml2-devel libxslt-devel \
                    tesseract tesseract-devel 2>/dev/null || true
            elif command -v pacman &>/dev/null; then
                sudo pacman -Sy --noconfirm python python-pip \
                    libxml2 libxslt tesseract 2>/dev/null || true
            elif command -v apk &>/dev/null; then
                apk add --no-cache python3 py3-pip \
                    libxml2-dev libxslt-dev \
                    tesseract-ocr 2>/dev/null || true
            fi
            ;;
        macos)
            if command -v brew &>/dev/null; then
                brew install python3 tesseract 2>/dev/null || true
            else
                echo "WARNING: Homebrew not found. Install from https://brew.sh"
                echo "Then run: brew install python3 tesseract"
            fi
            ;;
        android-termux)
            pkg update -y 2>/dev/null || true
            pkg install -y python clang libxml2 libxslt \
                libjpeg-turbo libpng 2>/dev/null || true
            ;;
    esac
}

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Python3 not found. Attempting to install prerequisites..."
    install_prereqs
fi

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 still not found after install attempt."
    echo "Please install Python >= ${PYTHON_MIN} manually."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PY_VER"

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "venv created at $VENV_DIR"
else
    echo "venv already exists at $VENV_DIR"
fi

# Activate and install
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet

echo ""
echo "--- Installing core dependencies ---"
pip install -r requirements.txt

echo ""
echo "=== Environment ready! ==="
echo ""
echo "Activate: source .venv/bin/activate"
echo "Run:      python wfh.py --help"
echo "Or:       wfh --help  (if installed via pip)"
echo ""
echo "Optional extras:"
echo "  pip install wfh-wordlist[docs]   # PDF/XLSX/DOCX parsing"
echo "  pip install wfh-wordlist[ocr]    # OCR/image text extraction"
echo "  pip install wfh-wordlist[full]   # All optional dependencies"

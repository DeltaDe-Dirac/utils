#!/bin/bash
#
# Setup script for yt2mp3 utility
# Supports: Linux, macOS, WSL
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
log_info "Detected operating system: $OS"

# Check Python
log_info "Checking Python 3..."
if check_command python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_success "Python 3 found: $PYTHON_VERSION"
else
    log_error "Python 3 is not installed"
    log_info "Please install Python 3.8 or higher:"
    if [[ "$OS" == "macos" ]]; then
        echo "  brew install python3"
    elif [[ "$OS" == "linux" ]]; then
        echo "  sudo apt-get install python3 python3-pip  # Debian/Ubuntu"
        echo "  OR: sudo yum install python3 python3-pip  # RHEL/CentOS"
    fi
    exit 1
fi

# Check yt-dlp
log_info "Checking yt-dlp..."
if check_command yt-dlp; then
    YT_DLP_VERSION=$(yt-dlp --version 2>&1)
    log_success "yt-dlp found: $YT_DLP_VERSION"
else
    log_warning "yt-dlp not found, installing..."
    if check_command pip3; then
        pip3 install --user yt-dlp
        log_success "yt-dlp installed successfully"
    elif check_command pip; then
        pip install --user yt-dlp
        log_success "yt-dlp installed successfully"
    else
        log_error "pip not found. Please install pip first."
        exit 1
    fi
fi

# Check ffmpeg
log_info "Checking ffmpeg..."
if check_command ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1)
    log_success "ffmpeg found: $FFMPEG_VERSION"
else
    log_warning "ffmpeg not found, installing..."
    
    if [[ "$OS" == "macos" ]]; then
        if check_command brew; then
            brew install ffmpeg
            log_success "ffmpeg installed via Homebrew"
        else
            log_error "Homebrew not found. Please install ffmpeg manually:"
            echo "  1. Install Homebrew: https://brew.sh"
            echo "  2. Then run: brew install ffmpeg"
            exit 1
        fi
    elif [[ "$OS" == "linux" ]]; then
        if check_command apt-get; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
            log_success "ffmpeg installed via apt"
        elif check_command yum || check_command dnf; then
            sudo yum install -y ffmpeg || sudo dnf install -y ffmpeg
            log_success "ffmpeg installed via yum/dnf"
        elif check_command pacman; then
            sudo pacman -S --noconfirm ffmpeg
            log_success "ffmpeg installed via pacman"
        else
            log_error "Package manager not detected. Please install ffmpeg manually."
            exit 1
        fi
    elif [[ "$OS" == "windows" ]]; then
        log_error "This is a Windows system. Please run setup.bat instead."
        exit 1
    fi
fi

# Verify installations
log_info "Verifying installations..."
ERRORS=0

if ! check_command yt-dlp; then
    log_error "yt-dlp verification failed"
    ERRORS=$((ERRORS + 1))
fi

if ! check_command ffmpeg; then
    log_error "ffmpeg verification failed"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    log_error "Setup completed with $ERRORS error(s)"
    exit 1
fi

# Create cache directory
CACHE_DIR="$(cd "$(dirname "$0")" && pwd)/yt2mp3/.cache"
mkdir -p "$CACHE_DIR"
log_success "Cache directory created: $CACHE_DIR"

# Final success message
echo ""
log_success "Setup completed successfully!"
echo ""
echo "You can now use yt2mp3:"
echo "  python yt2mp3/yt_to_mp3.py \"<youtube-url>\""
echo "  python yt2mp3/yt_to_mp3.py \"<youtube-url>\" 1m30s 2m45s  # Trimmed clip"
echo ""
echo "For help:"
echo "  python yt2mp3/yt_to_mp3.py --help"
echo ""

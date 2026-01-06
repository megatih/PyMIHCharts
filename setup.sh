#!/bin/bash

# PyMIHCharts Setup Script
# This script sets up a clean Python virtual environment and installs dependencies.

# Exit on error
set -e

echo "Starting PyMIHCharts setup..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install it and try again."
    exit 1
fi

# 2. Check for venv module
if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed. On Debian/Ubuntu, try: sudo apt install python3-venv"
    exit 1
fi

# 3. Check for PySide6 system dependencies (X11/Qt6 requirements)
echo "Checking for PySide6 system dependencies..."
MISSING_LIBS=()
REQUIRED_LIBS=(
    "libxcb-cursor.so.0"
    "libxkbcommon-x11.so.0"
    "libxcb-icccm.so.4"
    "libxcb-image.so.0"
    "libxcb-keysyms.so.1"
    "libxcb-render-util.so.0"
    "libxcb-xinerama.so.0"
)

# Helper to check for libraries via ldconfig
check_lib() {
    ldconfig -p | grep -q "$1"
}

for lib in "${REQUIRED_LIBS[@]}"; do
    if ! check_lib "$lib"; then
        MISSING_LIBS+=("$lib")
    fi
done

if [ ${#MISSING_LIBS[@]} -ne 0 ]; then
    echo "------------------------------------------------"
    echo "Warning: Some libraries required for PySide6 appear to be missing:"
    for lib in "${MISSING_LIBS[@]}"; do
        echo "  - $lib"
    done
    echo ""
    echo "To install these dependencies:"
    echo "  Debian/Ubuntu: sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0"
    echo "  Fedora:        sudo dnf install libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm"
    echo "  Arch Linux:    sudo pacman -S libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm"
    echo "------------------------------------------------"
    # We don't exit here as ldconfig might not find everything in all environments
fi

# 4. Create virtual environment
if [ -d "venv" ]; then
    echo "Found existing 'venv' directory. Re-creating environment..."
    rm -rf venv
fi

echo "Creating virtual environment in 'venv/'..."
python3 -m venv venv

# 4. Activate and install dependencies
echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Installing defaults..."
    pip install yfinance pandas PySide6
fi

echo "------------------------------------------------"
echo "Setup complete!"
echo "To run the application, use: ./run.sh"
echo "Or manually: source venv/bin/activate && python3 main.py"
echo "------------------------------------------------"

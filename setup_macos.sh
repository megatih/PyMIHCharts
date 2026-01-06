#!/bin/bash

# PyMIHCharts macOS Setup Script
# This script sets up a clean Python virtual environment and installs dependencies.

set -e

echo "Starting PyMIHCharts setup for macOS..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install it (e.g., brew install python) and try again."
    exit 1
fi

# 2. Create virtual environment
if [ -d "venv" ]; then
    echo "Found existing 'venv' directory. Re-creating environment..."
    rm -rf venv
fi

echo "Creating virtual environment in 'venv/'..."
python3 -m venv venv

# 3. Activate and install dependencies
echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install yfinance pandas PySide6
fi

echo "------------------------------------------------"
echo "Setup complete!"
echo "To run the application, use: ./run.sh"
echo "------------------------------------------------"

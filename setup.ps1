Write-Host "Starting PyMIHCharts setup for Windows (PowerShell)..." -ForegroundColor Cyan

# 1. Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH. Please install it from python.org."
    return
}

# 2. Create virtual environment
if (Test-Path venv) {
    Write-Host "Found existing 'venv' directory. Re-creating environment..."
    Remove-Item -Recurse -Force venv
}

Write-Host "Creating virtual environment in 'venv/'..."
python -m venv venv

# 3. Activate and install dependencies
Write-Host "Activating virtual environment and installing dependencies..."
& ./venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
    pip install -r requirements.txt
} else {
    pip install yfinance pandas PySide6
}

Write-Host "------------------------------------------------" -ForegroundColor Green
Write-Host "Setup complete!"
Write-Host "To run the application, use: ./run.ps1"
Write-Host "------------------------------------------------"

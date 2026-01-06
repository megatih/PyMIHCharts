@echo off
echo Starting PyMIHCharts setup for Windows (CMD)...

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from python.org and ensure 'Add to PATH' is checked.
    pause
    exit /b 1
)

:: 2. Create virtual environment
if exist venv (
    echo Found existing 'venv' directory. Re-creating environment...
    rmdir /s /q venv
)

echo Creating virtual environment in 'venv/'...
python -m venv venv

:: 3. Activate and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install yfinance pandas PySide6
)

echo ------------------------------------------------
echo Setup complete!
echo To run the application, use: run.bat
echo ------------------------------------------------
pause

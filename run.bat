@echo off
if not exist venv (
    echo Error: Virtual environment 'venv' not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python main.py

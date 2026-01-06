if (!(Test-Path venv)) {
    Write-Error "Virtual environment 'venv' not found. Please run ./setup.ps1 first."
    return
}
& ./venv/Scripts/Activate.ps1
python main.py

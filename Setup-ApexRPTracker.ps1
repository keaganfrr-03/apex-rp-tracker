# Apex RP Tracker - setup menu.
# Right-click this file and choose "Run with PowerShell", or double-click Setup.bat.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-Python {
    foreach ($cmd in @("py", "python")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) { return $cmd }
    }
    return $null
}

function Ensure-Venv {
    $py = Get-Python
    if (-not $py) {
        Write-Host "Python was not found. Install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "Tick 'Add Python to PATH' in the installer, then run this script again."
        return $false
    }
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        & $py -m venv .venv
    }
    return $true
}

function Install-Requirements {
    if (-not (Ensure-Venv)) { return $false }
    Write-Host "Installing requirements.txt..." -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Write-Host "Requirements installed." -ForegroundColor Green
    return $true
}

function Start-App {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        if (-not (Install-Requirements)) { return }
    }
    Write-Host "Starting Apex RP Tracker..." -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe main.py
}

function Build-Exe {
    if (-not (Ensure-Venv)) { return }
    & .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    & .\.venv\Scripts\python.exe -m pytest -q tests
    & .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name ApexRPTracker main.py
    Write-Host "Done: dist\ApexRPTracker\ApexRPTracker.exe" -ForegroundColor Green
}

do {
    Write-Host ""
    Write-Host "=== Apex RP Tracker ===" -ForegroundColor Yellow
    Write-Host " 1) Install requirements (requirements.txt)"
    Write-Host " 2) Run the app"
    Write-Host " 3) Install requirements, then run the app"
    Write-Host " 4) Build the .exe"
    Write-Host " 5) Quit"
    $choice = Read-Host "Choose 1-5"
    try {
        switch ($choice) {
            "1" { [void](Install-Requirements) }
            "2" { Start-App }
            "3" { if (Install-Requirements) { Start-App } }
            "4" { Build-Exe }
        }
    } catch {
        Write-Host "Something went wrong: $($_.Exception.Message)" -ForegroundColor Red
    }
} while ($choice -ne "5")

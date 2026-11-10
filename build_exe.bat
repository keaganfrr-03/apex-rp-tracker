@echo off
REM Builds dist\ApexRPTracker\ApexRPTracker.exe  (needs Python 3.10+ installed)
cd /d "%~dp0"
python -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-dev.txt || goto :err
python -m pytest -q tests || goto :err
pyinstaller --noconfirm --clean --windowed --name ApexRPTracker main.py || goto :err
echo.
echo Done. Your app is in dist\ApexRPTracker\ApexRPTracker.exe
pause
exit /b 0
:err
echo Build failed - see the messages above.
pause
exit /b 1

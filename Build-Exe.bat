@echo off
setlocal
rem ------------------------------------------------------------------------------------
rem Builds ApexRPTracker.exe ONCE (re-run it only after an update).
rem Everything is kept outside OneDrive so Windows does not sync or scan thousands of Qt
rem files, which is a big part of why a Python install in OneDrive feels slow.
rem   build tools : %LOCALAPPDATA%\ApexRPTracker\buildenv
rem   the app     : %LOCALAPPDATA%\Programs\ApexRPTracker\ApexRPTracker.exe
rem ------------------------------------------------------------------------------------

if not defined LOCALAPPDATA goto fail
set "HERE=%~dp0"
set "BASE=%LOCALAPPDATA%\ApexRPTracker"
set "BENV=%BASE%\buildenv"
set "OUT=%LOCALAPPDATA%\Programs\ApexRPTracker"

tasklist /fi "imagename eq ApexRPTracker.exe" 2>nul | find /i "ApexRPTracker.exe" >nul
if not errorlevel 1 goto running

if exist "%BENV%\Scripts\python.exe" goto have_env
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto nopython
echo Creating build environment (one time)...
%PY% -m venv "%BENV%"
if errorlevel 1 goto fail

:have_env
echo [1/3] Checking build tools (only downloads what is missing)...
"%BENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --no-warn-script-location -q -r "%HERE%requirements-build.txt"
if errorlevel 1 goto fail

echo [2/3] Building the exe (about a minute)...
"%BENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --log-level WARN --name ApexRPTracker ^
 --distpath "%BASE%\dist" --workpath "%BASE%\work" --specpath "%BASE%\work" --paths "%HERE%." ^
 --exclude-module tkinter ^
 --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtWebEngineQuick ^
 --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick --exclude-module PySide6.QtQuickWidgets --exclude-module PySide6.QtQuick3D ^
 --exclude-module PySide6.Qt3DCore --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtMultimediaWidgets ^
 --exclude-module PySide6.QtCharts --exclude-module PySide6.QtDataVisualization --exclude-module PySide6.QtPdf ^
 --exclude-module PySide6.QtPdfWidgets --exclude-module PySide6.QtSql ^
 "%HERE%main.py"
if errorlevel 1 goto fail
if not exist "%BASE%\dist\ApexRPTracker\ApexRPTracker.exe" goto fail

echo [3/3] Installing to %OUT%
robocopy "%BASE%\dist\ApexRPTracker" "%OUT%" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail

powershell -NoProfile -Command "$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut($d+'\Apex RP Tracker.lnk'); $s.TargetPath='%OUT%\ApexRPTracker.exe'; $s.WorkingDirectory='%OUT%'; $s.Save()" >nul 2>nul

echo.
echo  Done. Use the "Apex RP Tracker" shortcut on your Desktop from now on.
echo  Your RP and history are not touched (they live in %APPDATA%\ApexRPTracker).
start "" "%OUT%\ApexRPTracker.exe"
timeout /t 4 /nobreak >nul
exit /b 0

:running
echo.
echo  Apex RP Tracker is open. Close it, then run this again.
echo.
pause
exit /b 1

:nopython
echo.
echo  Python was not found. Install Python 3.10 or newer from https://www.python.org/downloads/
echo  and tick "Add python.exe to PATH" in the installer, then run this again.
echo  (No Python? Build the exe with the GitHub action instead - see README.md.)
echo.
pause
exit /b 1

:fail
echo.
echo  Something went wrong - see the messages above.
echo.
pause
exit /b 1

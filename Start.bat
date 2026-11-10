@echo off
setlocal
rem ------------------------------------------------------------------------------------
rem Apex RP Tracker launcher.
rem Opens the built .exe if you have one, otherwise runs from Python.
rem It NEVER reinstalls or updates anything that is already on your PC.
rem ------------------------------------------------------------------------------------

set "HERE=%~dp0"
set "EXE=%LOCALAPPDATA%\Programs\ApexRPTracker\ApexRPTracker.exe"
set "DIST_EXE=%HERE%dist\ApexRPTracker\ApexRPTracker.exe"
set "ENV_DIR=%LOCALAPPDATA%\ApexRPTracker\venv"

if exist "%EXE%" goto run_exe
if exist "%DIST_EXE%" goto run_dist
if exist "%HERE%.venv\Scripts\pythonw.exe" if exist "%HERE%.venv\Lib\site-packages\PySide6\QtWidgets.pyd" goto run_project_venv
if exist "%ENV_DIR%\Scripts\pythonw.exe" if exist "%ENV_DIR%\Lib\site-packages\PySide6\QtWidgets.pyd" goto run_env
goto install

:run_exe
start "" "%EXE%"
exit /b 0

:run_dist
start "" "%DIST_EXE%"
exit /b 0

:run_project_venv
cd /d "%HERE%"
start "" "%HERE%.venv\Scripts\pythonw.exe" main.py
exit /b 0

:run_env
cd /d "%HERE%"
start "" "%ENV_DIR%\Scripts\pythonw.exe" main.py
exit /b 0

:install
echo.
echo  Apex RP Tracker - first run only
echo  Setting up once (about a minute). After this it opens instantly.
echo  For the fastest start of all, run Build-Exe.bat once afterwards.
echo.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto nopython

%PY% -m venv "%ENV_DIR%"
if errorlevel 1 goto fail
"%ENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check --no-warn-script-location -r "%HERE%requirements.txt"
if errorlevel 1 goto fail
goto run_env

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

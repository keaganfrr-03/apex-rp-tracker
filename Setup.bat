@echo off
REM Double-click to open the setup menu (bypasses the PowerShell script block for this run only).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-ApexRPTracker.ps1"

# Apex RP Tracker - version 4

Local Windows desktop app (Python, PySide6, SQLite). Works fully offline.

## Easiest way
1. Install Python 3.10+ from python.org (tick "Add Python to PATH").
2. Double-click `Setup.bat` (or right-click `Setup-ApexRPTracker.ps1` > Run with PowerShell).
3. Pick 3 to install the requirements and start the app. Pick 4 to build the .exe.

## Make the .exe
Use option 4 in the setup menu, or double-click `build_exe.bat`. The app appears in `dist\ApexRPTracker\ApexRPTracker.exe`.
(No Python on your PC? Put this folder on GitHub and run the "Build Windows exe" action.)

## First start
Settings opens by itself. Enter your RP before your first logged match (or later use
"Set current RP..." on the dashboard), pick a target rank, set the season end date, and
CHECK the rank ladder against the game (Season 31 defaults are loaded). Tick "verified" once you have.

## Using it
Use "Match calculator..." to enter kills, assists, participation, placement and entry cost; it adds them up for you.
Type `+125` or `-45` and press Enter. Double-click any match to edit it. Day totals are
kept by calendar day, so the "today" figures reset at midnight and old days stay in History.

## Stream mode (OBS)
Click "Stream mode" on the dashboard. In OBS add a **Window Capture** source and pick "Apex RP Tracker - Stream".
Resize the window freely. Right-click it to hide the frame, toggle always-on-top, or use a green
background (add a Chroma Key filter in OBS to make it transparent).

## Badges
The app draws its own rank badges. To use the real in-game look, put your own PNG files in
`%APPDATA%\ApexRPTracker\badges` named like `gold_ii.png` (tier_division) or `gold.png`, `master.png`.
They are picked up automatically; anything missing is drawn by the app.

## Your data
`%APPDATA%\ApexRPTracker\apex_rp.db` and a `backups` folder (one automatic backup per day,
newest 30 kept; "Back up now" in Settings makes one on demand).

# Apex RP Tracker - version 5

Local Windows desktop app (Python, PySide6, SQLite). Works fully offline.

## Starting it
**Fastest (recommended): build the exe once.**
1. Double-click `Build-Exe.bat` (about 2 minutes, needs Python 3.10+ installed once).
2. It puts `ApexRPTracker.exe` in `%LOCALAPPDATA%\Programs\ApexRPTracker` and adds an
   **Apex RP Tracker** shortcut to your Desktop. Use that shortcut from now on. No Python, no setup, no installs.
3. After you get a new version of this folder, run `Build-Exe.bat` again (close the app first).

**No exe yet?** Double-click `Start.bat`. It uses the exe if it exists, otherwise it runs from Python.
It only installs anything if something is missing (first run only, about a minute), then it opens instantly.

**No Python at all?** Push this folder to GitHub and run the "Build Windows exe" action, then
download the `ApexRPTracker-windows` artifact and run `ApexRPTracker.exe` inside it.

## Your RP
New databases start at **7,140 RP (Gold II, 140 / 750, 610 to Gold I)**, taken from your in-game screen.
Your RP and every match are saved to `%APPDATA%\ApexRPTracker\apex_rp.db` the moment you add them, so they
survive closing the app, rebuilding the exe, and updating to a new version (v5 reads the same database as v4;
an untouched v4 database gets 7,140 once, anything you already entered is left alone).
If the number ever disagrees with the game, use **Set current RP...** on the dashboard.
Saving Settings never changes your RP unless you edit the "Current RP" box yourself.

## Using it
Type `+125` or `-45` and press Enter, or use "Match calculator..." to add up kills, assists, participation,
placement and entry cost. Double-click any match to edit it. Day totals are kept by calendar day, so the
"today" figures reset at midnight and old days stay in History.

## Stream mode (OBS)
Click "Stream mode". In OBS add a **Window Capture** source and pick "Apex RP Tracker - Stream".
Right-click the window to hide the frame, toggle always-on-top, or use a green background (chroma key).

## Badges
The app draws its own rank badges. To use the in-game look, put your own PNG files in
`%APPDATA%\ApexRPTracker\badges` named like `gold_ii.png` (tier_division) or `gold.png`, `master.png`.

## Settings
Season end date, target rank, the rank ladder and entry costs. The ladder defaults are Season 31 taken from guides;
tick "verified" once you have checked them against the game. A backup is made once a day
(newest 30 kept) in `%APPDATA%\ApexRPTracker\backups`; "Back up now" makes one on demand.

## Developing
`pip install -r requirements-dev.txt`, then `python -m pytest -q tests` and `python main.py`.

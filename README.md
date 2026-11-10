# Apex RP Tracker - version 7

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
New databases start at **7,307 RP (Gold II, 307 / 750, 443 to Gold I)**, taken from your in-game screen.
The first time v6 opens your existing database it sets your RP to 7,307 once (your matches are kept, and it
never does this again, so after that "Set current RP..." is the only way to change it).
Your RP and every match are saved to `%APPDATA%\ApexRPTracker\apex_rp.db` the moment you add them, so they
survive closing the app, rebuilding the exe, and updating to a new version (v6 reads the same database as v4 and v5).
If the number ever disagrees with the game, use **Set current RP...** on the dashboard.
Saving Settings never changes your RP unless you edit the "Current RP" box yourself.

## Using it
Type `+125` or `-45` and press Enter, or use "Match calculator..." to add up kills, assists, participation,
placement and entry cost. Double-click any match to edit it. Day totals are kept by calendar day, so the
"today" figures reset at midnight and old days stay in History.

## Daily goal and usual gain
The **Daily goal** is the RP left to your target divided by the season days left, worked out at the start of the day.
If you gain **more than today's goal**, the goal card turns green and switches to the new, lower goal per day
straight away (it is also on the goal bar as "tomorrow's goal"). The **Usual / day** card is your average net RP over
every day you played, so it moves up when you have a big day. Day totals are kept per calendar day.

## Sessions (automatic)
A session is one stretch of playing. It starts by itself with the first match you log, and **ends by itself** when you
stop: no match for 45 minutes (change this in Settings), or a new day. The Session panel on the dashboard shows
LIVE while you play and ENDED when you stop, with how long ago your last match was.
If you play again later, your next match starts a **new session with a new goal** (no button needed). Press
**New session** if you want to end one by hand. Sessions use the time each match was logged. History lists every session.

**Session goal:** the first session of a day aims for the day's goal. A later session aims for what is left of it, so it
is smaller if you already played. Once the day's goal is done, you get a fresh, smaller goal worked out from where you are.

## Saving
Every match, edit, delete and RP change is written to the database and confirmed straight away; the line under the
buttons reads **Saved to disk** (green) once it was read back from the file, or **NOT SAVED** (red) if it was not.
A plain-text copy of every change is also kept in `%APPDATA%\ApexRPTracker\rp_journal.csv`, and a backup is made when
you start the app (once a day) and every time you close it (newest 60 kept).

## Stream mode (OBS)
Click "Stream mode". In OBS add a **Window Capture** source and pick "Apex RP Tracker - Stream".
Right-click the window to hide the frame, toggle always-on-top, or use a green background (chroma key).

## Badges
The app draws its own rank badges. To use the in-game look, put your own PNG files in
`%APPDATA%\ApexRPTracker\badges` named like `gold_ii.png` (tier_division) or `gold.png`, `master.png`.

## Settings
Season end date, target rank, the rank ladder and entry costs. The ladder defaults are Season 31 taken from guides;
tick "verified" once you have checked them against the game. A backup is made once a day
and when you close the app (newest 60 kept) in `%APPDATA%\ApexRPTracker\backups`; "Back up now" makes one on demand.

## Developing
`pip install -r requirements-dev.txt`, then `python -m pytest -q tests` and `python main.py`.

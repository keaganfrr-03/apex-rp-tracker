"""SQLite storage. Everything lives in one local file."""
import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    played_at TEXT NOT NULL,
    day TEXT NOT NULL,
    delta INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_matches_day ON matches(day);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


@dataclass
class Match:
    id: int
    played_at: datetime
    day: str
    delta: int
    note: str


def _row(r) -> Match:
    return Match(r["id"], datetime.fromisoformat(r["played_at"]), r["day"], r["delta"], r["note"])


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA synchronous=FULL")      # every save is on disk before the app carries on
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.journal_path = self.path.with_name("rp_journal.csv")

    def close(self):
        self.conn.close()

    # ---- second copy of every change -----------------------------------
    def log(self, action: str, match_id=None, delta=None, note: str = ""):
        """Append one line to rp_journal.csv (a plain-text record of every change).
        It can never stop a save: if the file cannot be written the app just carries on."""
        try:
            rp = int(self.get_setting("start_rp", 0)) + self.total_delta()
            new = not self.journal_path.exists()
            with open(self.journal_path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["time", "action", "match_id", "rp_change", "note", "rp_after"])
                w.writerow([datetime.now().isoformat(timespec="seconds"), action,
                            "" if match_id is None else match_id, "" if delta is None else delta, note, rp])
        except (OSError, ValueError, sqlite3.Error):
            pass

    def disk_total(self) -> int:
        """Total match RP as read back by a separate connection: proof it is really saved."""
        c = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            return c.execute("SELECT COALESCE(SUM(delta),0) FROM matches").fetchone()[0]
        finally:
            c.close()

    # ---- matches -------------------------------------------------------
    def add_match(self, delta: int, note: str = "", when: datetime | None = None) -> int:
        when = when or datetime.now()
        cur = self.conn.execute(
            "INSERT INTO matches(played_at, day, delta, note) VALUES (?,?,?,?)",
            (when.isoformat(timespec="seconds"), when.date().isoformat(), int(delta), note.strip()))
        self.conn.commit()
        self.log("add", cur.lastrowid, int(delta), note.strip())
        return cur.lastrowid

    def update_match(self, match_id: int, delta: int, note: str, when: datetime):
        self.conn.execute(
            "UPDATE matches SET played_at=?, day=?, delta=?, note=? WHERE id=?",
            (when.isoformat(timespec="seconds"), when.date().isoformat(), int(delta), note.strip(), match_id))
        self.conn.commit()
        self.log("edit", match_id, int(delta), note.strip())

    def delete_match(self, match_id: int):
        r = self.conn.execute("SELECT delta, note FROM matches WHERE id=?", (match_id,)).fetchone()
        self.conn.execute("DELETE FROM matches WHERE id=?", (match_id,))
        self.conn.commit()
        self.log("delete", match_id, r["delta"] if r else None, r["note"] if r else "")

    def list_matches(self, day: str | None = None):
        q = "SELECT * FROM matches"
        args = ()
        if day:
            q += " WHERE day=?"
            args = (day,)
        q += " ORDER BY played_at, id"
        return [_row(r) for r in self.conn.execute(q, args)]

    def recent_matches(self, limit: int | None = None):
        """Newest first: [(Match, number_of_that_day, running_total_after_it)].

        One SQL query does the numbering and the running total, so the screen never has to
        load and add up every match in Python just to show the latest ten.
        """
        q = ("SELECT id, played_at, day, delta, note, n, run FROM ("
             " SELECT *, ROW_NUMBER() OVER (PARTITION BY day ORDER BY played_at, id) AS n,"
             "        SUM(delta) OVER (ORDER BY played_at, id) AS run FROM matches)"
             " ORDER BY played_at DESC, id DESC")
        args = ()
        if limit:
            q += " LIMIT ?"
            args = (int(limit),)
        return [(_row(r), r["n"], r["run"]) for r in self.conn.execute(q, args)]

    def match_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

    def last_match(self):
        r = self.conn.execute("SELECT * FROM matches ORDER BY played_at DESC, id DESC LIMIT 1").fetchone()
        return _row(r) if r else None

    def total_delta(self) -> int:
        return self.conn.execute("SELECT COALESCE(SUM(delta),0) FROM matches").fetchone()[0]

    def day_total(self, day: str):
        r = self.conn.execute("SELECT COALESCE(SUM(delta),0), COUNT(*) FROM matches WHERE day=?", (day,)).fetchone()
        return r[0], r[1]

    def daily_totals(self):
        """[(day, matches, net)] newest first. Past days are never changed by a new day starting."""
        return [(r[0], r[1], r[2]) for r in self.conn.execute(
            "SELECT day, COUNT(*), SUM(delta) FROM matches GROUP BY day ORDER BY day DESC")]

    # ---- settings ------------------------------------------------------
    def get_setting(self, key, default=None):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if r else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                          "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        self.conn.commit()

    # ---- backups -------------------------------------------------------
    def backup(self, dest_dir, keep: int = 60) -> Path:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / f"apex_rp_{datetime.now():%Y%m%d_%H%M%S}.db"
        out = sqlite3.connect(str(target))
        try:
            self.conn.backup(out)
        finally:
            out.close()
        files = sorted(dest_dir.glob("apex_rp_*.db"))
        for old in files[:-keep]:
            old.unlink(missing_ok=True)
        return target

    def has_backup_today(self, dest_dir) -> bool:
        return any(Path(dest_dir).glob(f"apex_rp_{datetime.now():%Y%m%d}_*.db"))

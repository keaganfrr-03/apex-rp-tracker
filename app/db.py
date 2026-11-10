"""SQLite storage. Everything lives in one local file."""
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
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ---- matches -------------------------------------------------------
    def add_match(self, delta: int, note: str = "", when: datetime | None = None) -> int:
        when = when or datetime.now()
        cur = self.conn.execute(
            "INSERT INTO matches(played_at, day, delta, note) VALUES (?,?,?,?)",
            (when.isoformat(timespec="seconds"), when.date().isoformat(), int(delta), note.strip()))
        self.conn.commit()
        return cur.lastrowid

    def update_match(self, match_id: int, delta: int, note: str, when: datetime):
        self.conn.execute(
            "UPDATE matches SET played_at=?, day=?, delta=?, note=? WHERE id=?",
            (when.isoformat(timespec="seconds"), when.date().isoformat(), int(delta), note.strip(), match_id))
        self.conn.commit()

    def delete_match(self, match_id: int):
        self.conn.execute("DELETE FROM matches WHERE id=?", (match_id,))
        self.conn.commit()

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
    def backup(self, dest_dir, keep: int = 30) -> Path:
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

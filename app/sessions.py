"""Play sessions. Matches played close together belong to one session. No Qt in here.

A new session starts when:
  * more than `gap_min` minutes passed since the last match, or
  * a new calendar day started (so "today" and "this session" never disagree), or
  * you pressed "New session" (a manual break).
A session is "live" while the last match was less than `gap_min` minutes ago and no break was made;
after that it is "ended" and the next match you log starts a fresh session by itself.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_GAP_MIN = 45


@dataclass
class Session:
    day: str            # calendar day, YYYY-MM-DD
    start: datetime     # time of the first match
    end: datetime       # time of the last match
    matches: int
    net: int

    @property
    def minutes(self) -> int:
        """Minutes from the first to the last match."""
        return int((self.end - self.start).total_seconds() // 60)


def split_sessions(matches, gap_min=DEFAULT_GAP_MIN, breaks=()):
    """matches: objects with .played_at and .delta, oldest first. Returns [Session], oldest first."""
    gap = timedelta(minutes=max(1, int(gap_min)))
    brks = sorted(breaks)
    out, cur, prev = [], None, None
    for m in matches:
        t = m.played_at
        new = (cur is None or t.date() != prev.date() or t - prev > gap
               or any(prev < b <= t for b in brks))
        if new:
            cur = Session(t.date().isoformat(), t, t, 0, 0)
            out.append(cur)
        cur.end = t
        cur.matches += 1
        cur.net += int(m.delta)
        prev = t
    return out


def current_session(sessions, now: datetime, gap_min=DEFAULT_GAP_MIN, breaks=(), day=None):
    """(session, live) for `day` (default: today): its latest session and whether it is still going."""
    today = (day or now.date()).isoformat()
    todays = [s for s in sessions if s.day == today]
    if not todays:
        return None, False
    last = todays[-1]
    gap = timedelta(minutes=max(1, int(gap_min)))
    live = (now - last.end <= gap) and not any(last.end < b <= now for b in breaks)
    return last, live


def parse_breaks(raw) -> list:
    """Breaks are stored as a JSON list of ISO times; bad entries are ignored."""
    import json
    try:
        items = json.loads(raw) if raw else []
    except ValueError:
        return []
    out = []
    for x in items:
        try:
            out.append(datetime.fromisoformat(x))
        except (TypeError, ValueError):
            pass
    return out

"""Ties the database, rank maths and goal maths together."""
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .db import Database
from .goals import GoalInfo, Projection, average_gain, daily_goal, project_finish, session_goal
from .sessions import DEFAULT_GAP_MIN, Session, current_session, parse_breaks, split_sessions
from .ranks import (DEFAULT_ENTRY_COSTS, DEFAULT_LADDER, SEASON_LABEL, RankInfo, rank_for,
                    target_options, validate_ladder)

# Your RP from the in-game screen: Gold II, 307 RP into a 750 RP division, 443 RP to Gold I
# (Gold II starts at 7,000, so 7,000 + 307). New databases start here.
DEFAULT_START_RP = 7307

DEFAULT_NOTE = (f"Default ladder for {SEASON_LABEL}, taken from guides (not from the game). "
                "Two guides put Gold IV at 5,250 instead of 5,500 - confirm in game.")


@dataclass
class SessionInfo:
    state: str                 # "none" = nothing played today, "live" = playing now, "ended" = stopped
    goal: int                  # goal of this session (live) or of the next one you start (none / ended)
    net: int = 0               # RP gained in the live session (0 when not live)
    matches: int = 0           # matches in the live session
    fraction: float = 0.0      # progress to the session goal, 0..1
    over: int = 0              # RP above the session goal
    count_today: int = 0       # sessions played today
    last: Session | None = None   # today's latest session (live or ended)
    minutes_since: int | None = None   # minutes since the last match today
    reached: bool = False      # season target reached, so no goal needed
    next_is_new: bool = False  # goal shown is for a session that has not started yet
    avg_net: int | None = None # usual RP per session (all sessions so far, the live one included)


@dataclass
class Snapshot:
    day: date
    current_rp: int
    today_net: int
    today_count: int
    rank: RankInfo
    target_label: str
    target_rp: int
    goal: GoalInfo
    season_end: date
    start_rp: int
    entry_cost: int
    thresholds_verified: bool
    thresholds_note: str
    avg_per_day: int | None = None    # usual RP per played day (None until a match is logged)
    avg_days: int = 0                 # how many days that average is over
    session: SessionInfo | None = None
    projection: Projection | None = None   # when you reach the target at your usual daily gain


class Tracker:
    def __init__(self, db: Database):
        self.db = db
        d = db.get_setting
        if d("start_rp") is None:
            db.set_setting("start_rp", DEFAULT_START_RP)
        if d("seeded_v5") is None:
            # A v4 database that was never filled in (0 RP, no matches) gets your RP once.
            # Anything you already entered is left exactly as it is.
            if int(d("start_rp")) == 0 and db.match_count() == 0:
                db.set_setting("start_rp", DEFAULT_START_RP)
            db.set_setting("seeded_v5", "1")
        if d("seeded_v6") is None:
            # v6: you said your RP is 7,307 now. Applied once; your match history is kept.
            self.set_current_rp(DEFAULT_START_RP)
            db.set_setting("seeded_v6", "1")
        if d("season_end") is None:
            db.set_setting("season_end", (date.today() + timedelta(days=60)).isoformat())
        if d("ladder") is None:   # new key: older versions stored a coarser table under "thresholds"
            db.set_setting("ladder", json.dumps(DEFAULT_LADDER))
            db.set_setting("thresholds_note", DEFAULT_NOTE)
            db.set_setting("thresholds_verified", "0")
        if d("entry_costs") is None:
            db.set_setting("entry_costs", json.dumps(DEFAULT_ENTRY_COSTS))
        if d("target_label") is None:
            db.set_setting("target_label", "Diamond IV")
        if d("setup_done") != "1":              # no welcome screen: everything has a sensible default
            db.set_setting("setup_done", "1")

    # ---- settings accessors -------------------------------------------
    @property
    def start_rp(self) -> int:
        return int(self.db.get_setting("start_rp", 0))

    @property
    def season_end(self) -> date:
        return date.fromisoformat(self.db.get_setting("season_end"))

    @property
    def ladder(self):
        return [(n, int(v)) for n, v in json.loads(self.db.get_setting("ladder"))]

    @property
    def entry_costs(self):
        return {k: int(v) for k, v in json.loads(self.db.get_setting("entry_costs")).items()}

    def save_settings(self, *, start_rp, season_end: date, target_label, ladder,
                      note, verified, entry_costs=None):
        validate_ladder(ladder)
        self.db.set_setting("ladder", json.dumps(ladder))
        if entry_costs is not None:
            self.db.set_setting("entry_costs", json.dumps(entry_costs))
        self.db.set_setting("start_rp", int(start_rp))
        self.db.set_setting("season_end", season_end.isoformat())
        self.db.set_setting("target_label", target_label)
        self.db.set_setting("thresholds_note", note)
        self.db.set_setting("thresholds_verified", "1" if verified else "0")
        self.db.set_setting("setup_done", "1")

    # ---- sessions -------------------------------------------------------
    @property
    def session_gap_min(self) -> int:
        try:
            return max(1, int(self.db.get_setting("session_gap_min", DEFAULT_GAP_MIN)))
        except ValueError:
            return DEFAULT_GAP_MIN

    def set_session_gap(self, minutes: int):
        self.db.set_setting("session_gap_min", max(1, int(minutes)))

    @property
    def session_breaks(self):
        return parse_breaks(self.db.get_setting("session_breaks", "[]"))

    def new_session(self, now: datetime | None = None):
        """Manual break: the next match you log starts a new session."""
        now = now or datetime.now()
        keep = [b.isoformat(timespec="seconds") for b in self.session_breaks][-200:]
        keep.append(now.isoformat(timespec="seconds"))
        self.db.set_setting("session_breaks", json.dumps(keep))
        self.db.log("new_session")

    def all_sessions(self):
        """Every session ever played, oldest first."""
        return split_sessions(self.db.list_matches(), self.session_gap_min, self.session_breaks)

    def reset_thresholds(self):
        self.db.set_setting("ladder", json.dumps(DEFAULT_LADDER))
        self.db.set_setting("entry_costs", json.dumps(DEFAULT_ENTRY_COSTS))
        self.db.set_setting("thresholds_note", DEFAULT_NOTE)
        self.db.set_setting("thresholds_verified", "0")

    def set_current_rp(self, rp: int):
        """Correct the total to match the game: adjusts the starting RP, keeps history."""
        self.db.set_setting("start_rp", int(rp) - self.db.total_delta())
        self.db.log("set_rp", None, None, f"current RP set to {int(rp)}")

    # ---- computed -----------------------------------------------------
    def current_rp(self) -> int:
        return self.start_rp + self.db.total_delta()

    def resolve_target(self):
        label = self.db.get_setting("target_label")
        opts = target_options(self.ladder)
        for lab, rp in opts:
            if lab == label:
                return lab, rp
        return opts[-1]

    def _session_info(self, today: date, now: datetime, cur: int, today_net: int,
                      goal: GoalInfo, t_rp: int) -> SessionInfo:
        gap, breaks = self.session_gap_min, self.session_breaks
        every = split_sessions(self.db.list_matches(), gap, breaks)
        todays = [x for x in every if x.day == today.isoformat()]
        last, live = current_session(todays, now, gap, breaks, today)
        since = None if last is None else max(0, int((now - last.end).total_seconds() // 60))
        net = last.net if live else 0
        before = today_net - net              # RP already gained today before this session began
        g = session_goal(goal.goal, before, cur - net, t_rp, goal.days_left)
        if goal.reached:
            frac = 1.0
        elif g <= 0:
            frac = 0.0
        else:
            frac = max(0.0, min(1.0, net / g))
        state = "none" if last is None else "live" if live else "ended"
        return SessionInfo(state=state, goal=g, net=net, matches=last.matches if live else 0,
                           fraction=frac, over=max(0, net - g) if g > 0 else 0,
                           count_today=len(todays), last=last, minutes_since=since,
                           reached=goal.reached, next_is_new=not live,
                           avg_net=round(sum(x.net for x in every) / len(every)) if every else None)

    def snapshot(self, today: date | None = None, now: datetime | None = None) -> Snapshot:
        now = now or datetime.now()
        today = today or now.date()
        net, count = self.db.day_total(today.isoformat())
        cur = self.current_rp()
        t_label, t_rp = self.resolve_target()
        totals = self.db.daily_totals()
        goal = daily_goal(cur, net, t_rp, self.season_end, today)
        return Snapshot(
            day=today, current_rp=cur, today_net=net, today_count=count,
            rank=rank_for(cur, self.ladder), target_label=t_label, target_rp=t_rp,
            goal=goal, session=self._session_info(today, now, cur, net, goal, t_rp),
            season_end=self.season_end, start_rp=self.start_rp,
            entry_cost=self.entry_costs.get(rank_for(cur, self.ladder).tier, 0),
            thresholds_verified=self.db.get_setting("thresholds_verified") == "1",
            thresholds_note=self.db.get_setting("thresholds_note", ""),
            avg_per_day=average_gain(totals), avg_days=len(totals),
            projection=project_finish(cur, t_rp, average_gain(totals), today, self.season_end))

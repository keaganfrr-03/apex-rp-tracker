"""Ties the database, rank maths and goal maths together."""
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .db import Database
from .goals import GoalInfo, daily_goal
from .ranks import (DEFAULT_ENTRY_COSTS, DEFAULT_LADDER, SEASON_LABEL, RankInfo, rank_for,
                    target_options, validate_ladder)

DEFAULT_NOTE = (f"Default ladder for {SEASON_LABEL}, taken from guides (not from the game). "
                "Two guides put Gold IV at 5,250 instead of 5,500 - confirm in game.")


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


class Tracker:
    def __init__(self, db: Database):
        self.db = db
        d = db.get_setting
        if d("start_rp") is None:
            db.set_setting("start_rp", 0)
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
        if d("setup_done") is None:
            db.set_setting("setup_done", "0")

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

    def reset_thresholds(self):
        self.db.set_setting("ladder", json.dumps(DEFAULT_LADDER))
        self.db.set_setting("entry_costs", json.dumps(DEFAULT_ENTRY_COSTS))
        self.db.set_setting("thresholds_note", DEFAULT_NOTE)
        self.db.set_setting("thresholds_verified", "0")

    def set_current_rp(self, rp: int):
        """Correct the total to match the game: adjusts the starting RP, keeps history."""
        self.db.set_setting("start_rp", int(rp) - self.db.total_delta())

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

    def snapshot(self, today: date | None = None) -> Snapshot:
        today = today or datetime.now().date()
        net, count = self.db.day_total(today.isoformat())
        cur = self.current_rp()
        t_label, t_rp = self.resolve_target()
        return Snapshot(
            day=today, current_rp=cur, today_net=net, today_count=count,
            rank=rank_for(cur, self.ladder), target_label=t_label, target_rp=t_rp,
            goal=daily_goal(cur, net, t_rp, self.season_end, today),
            season_end=self.season_end, start_rp=self.start_rp,
            entry_cost=self.entry_costs.get(rank_for(cur, self.ladder).tier, 0),
            thresholds_verified=self.db.get_setting("thresholds_verified") == "1",
            thresholds_note=self.db.get_setting("thresholds_note", ""))

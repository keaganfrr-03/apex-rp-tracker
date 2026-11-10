"""Dynamic daily RP goal."""
import math
from dataclasses import dataclass
from datetime import date


@dataclass
class GoalInfo:
    goal: int            # RP to gain today (stable through the day)
    remaining: int       # RP still needed to reach the target right now
    days_left: int       # season days left, counting today
    fraction: float      # today's progress towards the goal, 0..1
    reached: bool        # target already reached
    over: int = 0        # RP gained above today's goal (0 until the goal is beaten)
    next_goal: int | None = None   # per-day goal from tomorrow on, from your RP right now (None on the last day)

    @property
    def beaten(self) -> bool:
        return self.over > 0


def daily_goal(current_rp, today_net, target_rp, season_end: date, today: date) -> GoalInfo:
    days_left = max(1, (season_end - today).days + 1)
    start_of_day = current_rp - today_net
    remaining_at_start = max(0, target_rp - start_of_day)
    remaining_now = max(0, target_rp - current_rp)
    goal = math.ceil(remaining_at_start / days_left)
    reached = current_rp >= target_rp
    if goal <= 0:
        frac = 1.0 if reached else 0.0
    else:
        frac = max(0.0, min(1.0, today_net / goal))
    over = max(0, today_net - goal) if goal > 0 else 0
    days_after = days_left - 1
    # Tomorrow's goal is worked out from the RP you have right now, so every RP above (or below)
    # today's goal moves it straight away. It matches what the dashboard shows after midnight.
    next_goal = math.ceil(remaining_now / days_after) if days_after >= 1 else None
    return GoalInfo(goal, remaining_now, days_left, frac, reached, over, next_goal)


def average_gain(daily_totals) -> int | None:
    """Usual RP per played day: net RP over all days with matches. daily_totals = [(day, matches, net)]."""
    totals = [net for _, _, net in daily_totals]
    if not totals:
        return None
    return round(sum(totals) / len(totals))

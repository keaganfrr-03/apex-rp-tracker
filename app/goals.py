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
    return GoalInfo(goal, remaining_now, days_left, frac, reached)

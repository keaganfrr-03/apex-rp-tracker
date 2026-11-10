"""Rank ladder maths. No Qt in here, so it is easy to test.

The ladder is a flat list of (label, RP where that division starts), lowest first,
so uneven divisions (Platinum is 750/750/1000/1000) work. It is fully editable in Settings.
Defaults: Season 31 (Split 1), cross-checked across several guides. Two guides list
Gold IV at 5,250 instead of 5,500, so the app keeps a "verified" tick for you to confirm in game.
"""
from dataclasses import dataclass

SEASON_LABEL = "Season 31 (Split 1)"

TIERS = ["Rookie", "Bronze", "Silver", "Gold", "Platinum", "Diamond"]
DIVISIONS = ["IV", "III", "II", "I"]

# RP where each division starts. Master has no divisions and is the open-ended top.
_FLOORS = {
    "Rookie": [0, 250, 500, 750],
    "Bronze": [1000, 1500, 2000, 2500],
    "Silver": [3000, 3500, 4000, 4500],
    "Gold": [5500, 6250, 7000, 7750],
    "Platinum": [8500, 9250, 10000, 11000],
    "Diamond": [12000, 13000, 14000, 15000],
}
DEFAULT_LADDER = [(f"{t} {d}", rp) for t in TIERS for d, rp in zip(DIVISIONS, _FLOORS[t])]
DEFAULT_LADDER.append(("Master", 16000))

# RP charged to enter a match, by tier.
DEFAULT_ENTRY_COSTS = {"Rookie": 0, "Bronze": 10, "Silver": 20, "Gold": 38,
                       "Platinum": 48, "Diamond": 65, "Master": 90}


@dataclass
class RankInfo:
    tier: str
    division: str          # "" for Master
    label: str             # e.g. "Gold II" or "Master"
    start_rp: int          # RP where this division starts
    next_rp: int | None    # RP where the next division starts (None at the top)
    fraction: float        # 0..1 progress through this division


def tier_of(label: str) -> str:
    head, _, last = label.rpartition(" ")
    return head if last in DIVISIONS and head else label


def validate_ladder(ladder):
    if len(ladder) < 2:
        raise ValueError("You need at least two ranks.")
    if ladder[0][1] != 0:
        raise ValueError("The lowest rank must start at 0 RP.")
    for (_, a), (n, b) in zip(ladder, ladder[1:]):
        if b <= a:
            raise ValueError(f"{n} must start at a higher RP than the rank before it.")


def rank_for(rp, ladder=DEFAULT_LADDER) -> RankInfo:
    rp = max(0, int(rp))
    idx = 0
    for i, (_, floor) in enumerate(ladder):
        if rp >= floor:
            idx = i
    label, start = ladder[idx]
    tier = tier_of(label)
    div = label[len(tier):].strip()
    if idx == len(ladder) - 1:
        return RankInfo(tier, div, label, start, None, 1.0)
    nxt = ladder[idx + 1][1]
    return RankInfo(tier, div, label, start, nxt, max(0.0, min(1.0, (rp - start) / (nxt - start))))


def target_options(ladder=DEFAULT_LADDER):
    """All (label, rp) pairs the user can pick as a target."""
    return list(ladder)

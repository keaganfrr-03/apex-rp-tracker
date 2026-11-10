"""Match RP calculator and simple match statistics."""
from dataclasses import dataclass


def match_net(kills_rp=0, assists_rp=0, participation_rp=0, placement_rp=0, entry_cost=0) -> int:
    """Net RP for one game. entry_cost is entered as a positive number and is subtracted."""
    return int(kills_rp) + int(assists_rp) + int(participation_rp) + int(placement_rp) - abs(int(entry_cost))


@dataclass
class MatchStats:
    count: int
    ups: int       # matches that gained RP
    downs: int     # matches that lost RP
    best: int
    worst: int
    avg: int       # average RP per match, rounded


def match_stats(deltas):
    """Summary of a list of RP changes, or None when there are none."""
    d = [int(x) for x in deltas]
    if not d:
        return None
    return MatchStats(len(d), sum(1 for x in d if x > 0), sum(1 for x in d if x < 0),
                      max(d), min(d), round(sum(d) / len(d)))

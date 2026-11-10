"""Match RP calculator: add up the parts of one ranked game."""


def match_net(kills_rp=0, assists_rp=0, participation_rp=0, placement_rp=0, entry_cost=0) -> int:
    """Net RP for one game. entry_cost is entered as a positive number and is subtracted."""
    return int(kills_rp) + int(assists_rp) + int(participation_rp) + int(placement_rp) - abs(int(entry_cost))

import re

_RX = re.compile(r"^\s*([+\-\u2212]?)\s*(\d{1,5})\s*$")


def parse_rp(text: str) -> int:
    """'+125' -> 125, '-45' -> -45, '60' -> 60. Raises ValueError otherwise."""
    m = _RX.match(text or "")
    if not m:
        raise ValueError("Enter RP like +125 or -45.")
    value = int(m.group(2))
    if value > 9999:
        raise ValueError("That RP change looks too big.")
    return -value if m.group(1) in ("-", "\u2212") else value

"""Rank badges.

The app draws its own original badge-style medallions in each tier's colour, so it does not
ship any game artwork. If you want the real in-game look, drop your own PNG files into
    %APPDATA%\\ApexRPTracker\\badges
named like  gold_ii.png  (tier + division, lower case)  or  gold.png  (any division of that tier).
Master is  master.png.  Custom images are used automatically; anything missing is drawn.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF)

from .. import paths

TIER_COLORS = {
    "Rookie": "#9a8f85", "Bronze": "#c27c3e", "Silver": "#c3ccd8", "Gold": "#f0b429",
    "Platinum": "#4fd1d9", "Diamond": "#5b8cff", "Master": "#b45cf0", "Apex Predator": "#e8453c",
}
_cache = {}


def tier_color(tier: str) -> str:
    return TIER_COLORS.get(tier, "#9a8f85")


def _custom(tier, division, size):
    d = paths.data_dir() / "badges"
    names = []
    if division:
        names.append(f"{tier.lower()}_{division.lower()}.png")
    names.append(f"{tier.lower()}.png")
    for n in names:
        f = d / n
        if f.exists():
            pm = QPixmap(str(f))
            if not pm.isNull():
                return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None


def _draw(tier, division, size) -> QPixmap:
    s = float(size)
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    c = QColor(tier_color(tier))
    light, dark = c.lighter(150), c.darker(250)

    def grad(a, b):
        g = QLinearGradient(0, 0, 0, s)
        g.setColorAt(0, a)
        g.setColorAt(1, b)
        return QBrush(g)

    cx = cy = s / 2
    # outer medallion ring
    p.setPen(QPen(c.darker(160), s * 0.018))
    p.setBrush(grad(light, c.darker(140)))
    p.drawEllipse(QPointF(cx, cy), s * 0.47, s * 0.47)
    # dark inner disc
    p.setPen(QPen(c, s * 0.014))
    p.setBrush(QBrush(QColor(dark.red() // 2 + 12, dark.green() // 2 + 12, dark.blue() // 2 + 14)))
    p.drawEllipse(QPointF(cx, cy), s * 0.37, s * 0.37)
    if tier in ("Master", "Apex Predator"):          # extra outer ring for the top tiers
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(light, s * 0.012, Qt.DashLine))
        p.drawEllipse(QPointF(cx, cy), s * 0.43, s * 0.43)

    # chevron emblem
    def poly(pts):
        return QPolygonF([QPointF(x * s, y * s) for x, y in pts])

    p.setPen(QPen(c.darker(170), s * 0.01))
    p.setBrush(grad(light, c))
    p.drawPolygon(poly([(0.50, 0.19), (0.76, 0.60), (0.60, 0.60), (0.50, 0.44), (0.40, 0.60), (0.24, 0.60)]))
    p.setBrush(grad(c, c.darker(150)))
    p.drawPolygon(poly([(0.50, 0.50), (0.60, 0.66), (0.50, 0.62), (0.40, 0.66)]))

    # division plate
    if division:
        r = s * 0.14
        p.setPen(QPen(c, s * 0.015))
        p.setBrush(QBrush(QColor("#15171b")))
        p.drawEllipse(QPointF(cx, s * 0.80), r, r)
        f = QFont("Bahnschrift", 1)
        f.setBold(True)
        f.setPixelSize(max(8, int(s * 0.15)))
        p.setFont(f)
        p.setPen(QColor("#ffffff"))
        p.drawText(QRectF(cx - r, s * 0.80 - r, 2 * r, 2 * r), Qt.AlignCenter, division)
    p.end()
    return pm


def badge_pixmap(tier: str, division: str = "", size: int = 96) -> QPixmap:
    key = (tier, division, size)
    if key not in _cache:
        _cache[key] = _custom(tier, division, size) or _draw(tier, division, size)
    return _cache[key]


def clear_cache():
    _cache.clear()

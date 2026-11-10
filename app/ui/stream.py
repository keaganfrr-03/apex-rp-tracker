"""Compact, resizable, always-on-top window for OBS (Window Capture)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QVBoxLayout, QWidget

from ..ranks import split_label
from .badges import badge_pixmap, tier_color
from .theme import GREEN, NEUTRAL, RED, fmt_delta, rp_color


class _Panel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(0)
        self.title, self.value, self.sub = QLabel(""), QLabel(""), QLabel("")
        for w in (self.title, self.value, self.sub):
            w.setAlignment(Qt.AlignCenter)
            lay.addWidget(w)


class StreamWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Apex RP Tracker - Stream")
        self.resize(780, 120)
        self.setMinimumSize(380, 64)
        self._green, self._snap = False, None
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)
        self.badge = QLabel()
        self.cur, self.tgt, self.today = _Panel(), _Panel(), _Panel()
        row.addWidget(self.badge)
        row.addWidget(self.cur, 3)
        row.addWidget(self.tgt, 3)
        row.addWidget(self.today, 3)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self._restyle()

    # ---- right-click menu ---------------------------------------------
    def _menu(self, pos):
        m = QMenu(self)
        top = m.addAction("Always on top")
        top.setCheckable(True)
        top.setChecked(bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
        frameless = m.addAction("Hide window frame")
        frameless.setCheckable(True)
        frameless.setChecked(bool(self.windowFlags() & Qt.FramelessWindowHint))
        green = m.addAction("Green background (chroma key)")
        green.setCheckable(True)
        green.setChecked(self._green)
        m.addSeparator()
        close = m.addAction("Close stream window")
        a = m.exec(self.mapToGlobal(pos))
        if a is top:
            self.set_flag(Qt.WindowStaysOnTopHint, top.isChecked())
        elif a is frameless:
            self.set_flag(Qt.FramelessWindowHint, frameless.isChecked())
        elif a is green:
            self._green = green.isChecked()
            self._restyle()
        elif a is close:
            self.close()

    def set_flag(self, flag, on):
        self.setWindowFlag(flag, on)
        self.show()

    # ---- drawing ------------------------------------------------------
    def resizeEvent(self, e):
        self._restyle()
        super().resizeEvent(e)

    def _restyle(self):
        h = max(64, self.height())
        big, small = max(14, int(h * 0.30)), max(8, int(h * 0.105))
        bg = "#00b140" if self._green else "#0b0c0f"
        self.setStyleSheet(
            f"QWidget {{ background:{bg}; color:#f2f2f2; font-family:'Bahnschrift','Segoe UI',sans-serif; }}"
            f"QFrame#panel {{ background:#14161b; border:1px solid #6b2323; border-left:4px solid #e8453c; }}")
        for pnl in (self.cur, self.tgt, self.today):
            pnl.title.setStyleSheet(f"background:transparent;color:#aab0bb;font-size:{small}px;letter-spacing:1px;")
            pnl.sub.setStyleSheet(f"background:transparent;color:#aab0bb;font-size:{small}px;")
            pnl.value.setStyleSheet(f"background:transparent;font-size:{big}px;font-weight:bold;")
        self.badge.setStyleSheet("background:transparent;")
        if self._snap is not None:
            self._paint(self._snap)

    def refresh(self, s):
        self._snap = s
        self._paint(s)

    def _paint(self, s):
        h = max(64, self.height())
        tier, div = s.rank.tier, s.rank.division
        self.badge.setPixmap(badge_pixmap(tier, div, int(h * 0.80)))
        self.cur.title.setText("CURRENT RP")
        self.cur.value.setText(f"{s.current_rp:,}")
        self.cur.sub.setText(s.rank.label.upper())
        self.tgt.title.setText(f"TARGET  {s.target_label.upper()}")
        self.tgt.value.setText(f"{s.target_rp:,}")
        self.tgt.value.setStyleSheet(self.tgt.value.styleSheet() + f"color:{tier_color(split_label(s.target_label)[0])};")
        self.tgt.sub.setText("TARGET REACHED" if s.goal.reached else f"{s.goal.remaining:,} RP TO GO")
        self.today.title.setText("TODAY'S GAIN/LOSS")
        self.today.value.setText(fmt_delta(s.today_net))
        self.today.value.setStyleSheet(self.today.value.styleSheet() + f"color:{rp_color(s.today_net)};")
        g = s.goal
        if g.reached:
            self.today.sub.setText("GOAL DONE")
        elif g.beaten and g.next_goal is not None:
            self.today.sub.setText(f"GOAL BEATEN +{g.over:,}  NEW GOAL +{g.next_goal:,}")
        elif g.beaten:
            self.today.sub.setText(f"GOAL BEATEN +{g.over:,}")
        else:
            self.today.sub.setText(f"GOAL +{g.goal:,}  ({int(g.fraction * 100)}%)")

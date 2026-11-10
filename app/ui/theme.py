GREEN = "#2ecc71"
RED = "#ff5252"
NEUTRAL = "#c9ced6"
AMBER = "#f5a623"


def rp_color(value: int) -> str:
    return GREEN if value > 0 else RED if value < 0 else NEUTRAL


def fmt_delta(value: int) -> str:
    return f"+{value:,}" if value > 0 else f"{value:,}".replace("-", "-")


ACCENT = "#e8453c"

STYLE = f"""
QWidget {{ background:#0f1114; color:#e9ebef; font-family:'Bahnschrift','Segoe UI',sans-serif; font-size:14px; }}
QTabWidget::pane {{ border:0; }}
QTabBar::tab {{ background:#171a20; padding:9px 24px; margin-right:2px; color:#8c94a3; letter-spacing:1px; }}
QTabBar::tab:selected {{ background:#1f232b; color:#ffffff; border-bottom:2px solid {ACCENT}; }}
QFrame#card {{ background:#15181d; border:1px solid #272c35; border-left:4px solid {ACCENT}; border-radius:4px; }}
QFrame#hero {{ background:#14171c; border:1px solid #272c35; border-radius:6px; }}
QLabel#cardTitle {{ color:#8c94a3; font-size:12px; letter-spacing:1px; background:transparent; }}
QLabel#cardSub {{ color:#8c94a3; font-size:12px; background:transparent; }}
QLabel#cardValue {{ font-size:32px; font-weight:600; background:transparent; }}
QLabel#heroBig {{ font-size:46px; font-weight:700; background:transparent; }}
QLabel#heroCaption {{ color:#aab0bb; font-size:15px; letter-spacing:1px; background:transparent; }}
QLabel#warn {{ color:{AMBER}; background:transparent; }}
QLabel {{ background:transparent; }}
QLineEdit, QSpinBox, QComboBox, QDateEdit, QDateTimeEdit {{ background:#0b0d10; border:1px solid #303744; border-radius:4px; padding:7px 9px; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border:1px solid {ACCENT}; }}
QPushButton {{ background:#232832; border:0; border-radius:4px; padding:8px 16px; letter-spacing:1px; }}
QPushButton:hover {{ background:#2f3643; }}
QPushButton#primary {{ background:{ACCENT}; color:white; font-weight:600; }}
QPushButton#primary:hover {{ background:#f05a50; }}
QPushButton#danger {{ background:#5a2a2e; }}
QPushButton#danger:hover {{ background:#7a343a; }}
QProgressBar {{ background:#0b0d10; border:1px solid #272c35; border-radius:3px; height:16px; text-align:center; color:#e9ebef; font-size:11px; }}
QProgressBar::chunk {{ background:{ACCENT}; border-radius:2px; }}
QTableWidget {{ background:#15181d; alternate-background-color:#191d23; border:1px solid #272c35; gridline-color:#272c35; }}
QHeaderView::section {{ background:#1f232b; color:#8c94a3; border:0; padding:6px; letter-spacing:1px; }}
QTableWidget::item:selected {{ background:#4a2326; }}
"""

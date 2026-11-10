GREEN = "#2ecc71"
RED = "#ff5252"
NEUTRAL = "#c9ced6"
AMBER = "#f5a623"


def rp_color(value: int) -> str:
    return GREEN if value > 0 else RED if value < 0 else NEUTRAL


def fmt_delta(value: int) -> str:
    return f"+{value:,}" if value > 0 else f"{value:,}".replace("-", "-")


STYLE = f"""
QWidget {{ background:#14171c; color:#e6e9ef; font-family:'Segoe UI',sans-serif; font-size:14px; }}
QTabWidget::pane {{ border:0; }}
QTabBar::tab {{ background:#1b2027; padding:9px 22px; margin-right:2px; border-radius:6px 6px 0 0; color:#9aa4b2; }}
QTabBar::tab:selected {{ background:#232a33; color:#ffffff; }}
QFrame#card {{ background:#1b2027; border:1px solid #2a323d; border-radius:12px; }}
QLabel#cardTitle {{ color:#9aa4b2; font-size:12px; background:transparent; }}
QLabel#cardSub {{ color:#9aa4b2; font-size:12px; background:transparent; }}
QLabel#cardValue {{ font-size:30px; font-weight:600; background:transparent; }}
QLabel#warn {{ color:{AMBER}; background:transparent; }}
QLabel {{ background:transparent; }}
QLineEdit, QSpinBox, QComboBox, QDateEdit, QDateTimeEdit {{ background:#10131a; border:1px solid #2f3946; border-radius:8px; padding:7px 9px; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border:1px solid #4c8dff; }}
QPushButton {{ background:#2a323d; border:0; border-radius:8px; padding:8px 16px; }}
QPushButton:hover {{ background:#344050; }}
QPushButton#primary {{ background:#3b82f6; color:white; font-weight:600; }}
QPushButton#primary:hover {{ background:#5593f8; }}
QPushButton#danger {{ background:#5a2a2e; }}
QPushButton#danger:hover {{ background:#7a343a; }}
QProgressBar {{ background:#10131a; border:1px solid #2a323d; border-radius:7px; height:16px; text-align:center; color:#e6e9ef; font-size:11px; }}
QProgressBar::chunk {{ background:#3b82f6; border-radius:6px; }}
QTableWidget {{ background:#1b2027; alternate-background-color:#1f252d; border:1px solid #2a323d; border-radius:8px; gridline-color:#2a323d; }}
QHeaderView::section {{ background:#232a33; color:#9aa4b2; border:0; padding:6px; }}
QTableWidget::item:selected {{ background:#2b4a7a; }}
"""

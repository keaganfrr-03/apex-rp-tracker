GREEN = "#2ecc71"
RED = "#ff5252"
NEUTRAL = "#c9ced6"
AMBER = "#f5a623"
ACCENT = "#e8453c"
MUTED = "#8b93a1"

# surfaces, darkest to lightest
BG = "#0d0f13"
SURFACE = "#14171d"
SURFACE2 = "#1a1e26"
BORDER = "#262b35"
BORDER_HI = "#363d4a"


def rp_color(value: int) -> str:
    return GREEN if value > 0 else RED if value < 0 else NEUTRAL


def fmt_delta(value: int) -> str:
    return f"+{value:,}" if value > 0 else f"{value:,}".replace("-", "-")


STYLE = f"""
QWidget {{ background:{BG}; color:#e8eaee; font-family:'Bahnschrift','Segoe UI',sans-serif; font-size:14px; }}
QLabel {{ background:transparent; }}
QToolTip {{ background:{SURFACE2}; color:#e8eaee; border:1px solid {BORDER_HI}; padding:5px 8px; }}

/* tabs */
QTabWidget::pane {{ border:0; border-top:1px solid {BORDER}; }}
QTabBar {{ background:{BG}; }}
QTabBar::tab {{ background:transparent; padding:11px 26px; margin-right:4px; color:{MUTED};
               border-bottom:2px solid transparent; }}
QTabBar::tab:hover {{ color:#ffffff; background:{SURFACE}; }}
QTabBar::tab:selected {{ background:{SURFACE}; color:#ffffff; border-bottom:2px solid {ACCENT}; }}

/* cards and panels */
QFrame#card {{ background:{SURFACE}; border:1px solid {BORDER}; border-left:3px solid {ACCENT}; border-radius:8px; }}
QFrame#hero {{ background:{SURFACE}; border:1px solid {BORDER}; border-left:3px solid {ACCENT}; border-radius:10px; }}
QFrame#entryBar {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:8px; }}
QLabel#cardTitle {{ color:{MUTED}; font-size:11px; font-weight:600; letter-spacing:1px; background:transparent; }}
QLabel#cardSub {{ color:{MUTED}; font-size:12px; background:transparent; }}
QLabel#cardValue {{ font-size:30px; font-weight:600; background:transparent; }}
QLabel#heroBig {{ font-size:48px; font-weight:700; background:transparent; }}
QLabel#heroCaption {{ color:#aab0bb; font-size:13px; font-weight:600; letter-spacing:2px; background:transparent; }}
QLabel#appTitle {{ font-size:22px; font-weight:700; background:transparent; }}
QLabel#section {{ color:{MUTED}; font-size:12px; font-weight:600; letter-spacing:1px; padding-top:4px; background:transparent; }}
QLabel#barLabel {{ color:#c4c9d2; font-size:13px; background:transparent; }}
QLabel#warn {{ color:{AMBER}; background:transparent; }}

/* inputs */
QLineEdit, QSpinBox, QComboBox, QDateEdit, QDateTimeEdit {{ background:#0a0c0f; border:1px solid {BORDER_HI}; border-radius:6px;
                                                           padding:7px 10px; selection-background-color:{ACCENT}; }}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover, QDateEdit:hover, QDateTimeEdit:hover {{ border:1px solid #4a5363; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus {{ border:1px solid {ACCENT}; }}
QComboBox QAbstractItemView {{ background:{SURFACE2}; border:1px solid {BORDER_HI}; selection-background-color:#4a2326; }}
QCheckBox {{ spacing:8px; background:transparent; }}
QCheckBox::indicator {{ width:16px; height:16px; border:1px solid {BORDER_HI}; border-radius:4px; background:#0a0c0f; }}
QCheckBox::indicator:checked {{ background:{ACCENT}; border:1px solid {ACCENT}; }}

/* buttons */
QPushButton {{ background:{SURFACE2}; border:1px solid {BORDER}; border-radius:6px; padding:8px 16px; }}
QPushButton:hover {{ background:#262c37; border:1px solid {BORDER_HI}; }}
QPushButton:pressed {{ background:#1f242d; }}
QPushButton:disabled {{ color:#5b6270; background:{SURFACE}; }}
QPushButton#primary {{ background:{ACCENT}; border:1px solid {ACCENT}; color:#ffffff; font-weight:600; }}
QPushButton#primary:hover {{ background:#f05a50; border:1px solid #f05a50; }}
QPushButton#primary:pressed {{ background:#cf3b33; }}
QPushButton#danger {{ background:#4a2226; border:1px solid #5f2c31; }}
QPushButton#danger:hover {{ background:#6a2f35; }}

/* progress bars */
QProgressBar {{ background:#0a0c0f; border:1px solid {BORDER}; border-radius:9px; height:18px; text-align:center;
               color:#e8eaee; font-size:11px; }}
QProgressBar::chunk {{ background:{ACCENT}; border-radius:8px; }}

/* tables */
QTableWidget {{ background:{SURFACE}; alternate-background-color:#171a21; border:1px solid {BORDER}; border-radius:8px;
               gridline-color:transparent; outline:0; }}
QTableWidget::item {{ padding:3px 8px; border:0; }}
QTableWidget::item:selected {{ background:#4a2326; color:#ffffff; }}
QHeaderView {{ background:transparent; }}
QHeaderView::section {{ background:{SURFACE2}; color:{MUTED}; border:0; border-bottom:1px solid {BORDER}; padding:8px 8px;
                       font-size:12px; font-weight:600; }}
QTableCornerButton::section {{ background:{SURFACE2}; border:0; }}

/* scrollbars */
QScrollBar:vertical {{ background:transparent; width:12px; margin:2px; }}
QScrollBar::handle:vertical {{ background:{BORDER_HI}; border-radius:4px; min-height:28px; }}
QScrollBar::handle:vertical:hover {{ background:#4a5363; }}
QScrollBar:horizontal {{ background:transparent; height:12px; margin:2px; }}
QScrollBar::handle:horizontal {{ background:{BORDER_HI}; border-radius:4px; min-width:28px; }}
QScrollBar::handle:horizontal:hover {{ background:#4a5363; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:transparent; }}

QSplitter::handle {{ background:transparent; }}
QMessageBox, QDialog, QInputDialog {{ background:{BG}; }}
"""

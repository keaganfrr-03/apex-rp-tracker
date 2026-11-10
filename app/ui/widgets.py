from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QSpinBox, QPushButton, QHBoxLayout, QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QFrame,
                               QLabel, QLineEdit, QMessageBox, QProgressBar, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QAbstractItemView, QHeaderView)

from ..calc import match_net
from ..ranks import split_label
from .badges import badge_pixmap, tier_color
from ..parsing import parse_rp
from .theme import NEUTRAL, fmt_delta, rp_color


class Card(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.value = QLabel("-")
        self.value.setObjectName("cardValue")
        self.sub = QLabel("")
        self.sub.setObjectName("cardSub")
        for w in (self.title, self.value, self.sub):
            lay.addWidget(w)

    def set(self, value, sub="", color=None):
        self.value.setText(value)
        self.value.setStyleSheet(f"color:{color or '#e6e9ef'};")
        self.sub.setText(sub)


def make_bar(fmt="%p%"):
    b = QProgressBar()
    b.setRange(0, 1000)
    b.setFormat(fmt)
    return b


def set_bar(bar, fraction, fmt=None, color=None):
    bar.setValue(int(max(0.0, min(1.0, fraction)) * 1000))
    if fmt is not None:
        bar.setFormat(fmt)
    c = color or "#e8453c"
    bar.setStyleSheet(f"QProgressBar::chunk {{ background:{c}; border-radius:6px; }}")


def colored_item(text, color=None, align=Qt.AlignRight):
    it = QTableWidgetItem(text)
    it.setForeground(QColor(color or NEUTRAL))
    it.setTextAlignment(align | Qt.AlignVCenter)
    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    return it


def make_table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t


def fill_matches(table, rows, start_rp):
    """rows come from Database.recent_matches(): newest first, (match, number of the day, running total)."""
    table.setUpdatesEnabled(False)
    table.setRowCount(len(rows))
    for r, (m, n, run) in enumerate(rows):
        cells = [colored_item(m.played_at.strftime("%a %d %b"), align=Qt.AlignLeft),
                 colored_item(f"#{n}  {m.played_at:%H:%M}", align=Qt.AlignLeft),
                 colored_item(fmt_delta(m.delta), rp_color(m.delta)),
                 colored_item(f"{start_rp + run:,}"),
                 colored_item(m.note, align=Qt.AlignLeft)]
        for c, it in enumerate(cells):
            table.setItem(r, c, it)
        table.item(r, 0).setData(Qt.UserRole, m.id)
    table.setUpdatesEnabled(True)


def selected_match_id(table):
    rows = table.selectionModel().selectedRows()
    if not rows:
        return None
    return table.item(rows[0].row(), 0).data(Qt.UserRole)


class EditMatchDialog(QDialog):
    def __init__(self, match, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit match")
        form = QFormLayout(self)
        self.delta = QLineEdit(fmt_delta(match.delta))
        self.note = QLineEdit(match.note)
        self.when = QDateTimeEdit(match.played_at)
        self.when.setCalendarPopup(True)
        self.when.setDisplayFormat("yyyy-MM-dd HH:mm")
        form.addRow("RP change", self.delta)
        form.addRow("Note", self.note)
        form.addRow("Played at", self.when)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        self.result_values = None

    def _ok(self):
        try:
            d = parse_rp(self.delta.text())
        except ValueError as e:
            QMessageBox.warning(self, "Check the RP", str(e))
            return
        self.result_values = (d, self.note.text(), self.when.dateTime().toPython())
        self.accept()


class CalculatorDialog(QDialog):
    """Enter the parts of one game; the net RP is added up for you."""
    def __init__(self, parent=None, entry_cost=0):
        super().__init__(parent)
        self.setWindowTitle("Match calculator")
        form = QFormLayout(self)
        self.fields = {}
        for key, label in (("kills", "Kills RP"), ("assists", "Assists RP"),
                           ("participation", "Participation RP"), ("placement", "Placement RP"),
                           ("entry", "Entry cost (enter as a positive number)")):
            sb = QSpinBox()
            sb.setRange(0, 999)
            sb.valueChanged.connect(self._update)
            self.fields[key] = sb
            form.addRow(label, sb)
        self.fields["entry"].setValue(entry_cost)
        self.place = QLineEdit()
        self.place.setPlaceholderText("Placement, e.g. 8 (for the note)")
        form.addRow("Placement #", self.place)
        self.total = QLabel("")
        self.total.setStyleSheet("font-size:22px;font-weight:600;")
        form.addRow("Net RP", self.total)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Add match")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        self._update()

    def net(self):
        f = {k: v.value() for k, v in self.fields.items()}
        return match_net(f["kills"], f["assists"], f["participation"], f["placement"], f["entry"])

    def note(self):
        f = {k: v.value() for k, v in self.fields.items()}
        place = self.place.text().strip().lstrip("#")
        base = f"K{f['kills']} A{f['assists']} P{f['participation']} place{f['placement']} entry-{f['entry']}"
        return (f"#{place}  " if place else "") + base

    def _update(self):
        n = self.net()
        self.total.setText(fmt_delta(n))
        self.total.setStyleSheet(f"font-size:22px;font-weight:600;color:{rp_color(n)};")


class RankHero(QFrame):
    """Like the in-game ranked screen: badge, last match RP, bar, next badge."""
    def __init__(self):
        super().__init__()
        self.setObjectName("hero")
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(18)
        self.cur = QLabel()
        self.cur.setFixedSize(112, 112)
        mid = QVBoxLayout()
        mid.setSpacing(2)
        self.big = QLabel("-")
        self.big.setObjectName("heroBig")
        self.caption = QLabel("")
        self.caption.setObjectName("heroCaption")
        self.bar = make_bar("")
        bl = QHBoxLayout()
        self.left, self.right = QLabel(""), QLabel("")
        self.right.setAlignment(Qt.AlignRight)
        bl.addWidget(self.left)
        bl.addWidget(self.right)
        mid.addWidget(self.big)
        mid.addWidget(self.caption)
        mid.addSpacing(4)
        mid.addWidget(self.bar)
        mid.addLayout(bl)
        right = QVBoxLayout()
        self.nxt = QLabel()
        self.nxt.setFixedSize(84, 84)
        self.to_next = QLabel("")
        self.to_next.setAlignment(Qt.AlignCenter)
        right.addWidget(self.nxt, 0, Qt.AlignCenter)
        right.addWidget(self.to_next)
        row.addWidget(self.cur)
        row.addLayout(mid, 1)
        row.addLayout(right)

    def set(self, s, last_delta):
        r = s.rank
        self.cur.setPixmap(badge_pixmap(r.tier, r.division, 112))
        if last_delta is None:
            self.big.setText("-")
            self.big.setStyleSheet("")
            self.caption.setText("NO MATCHES LOGGED YET")
        else:
            self.big.setText(fmt_delta(last_delta))
            self.big.setStyleSheet(f"color:{rp_color(last_delta)};")
            self.caption.setText("RANKED POINTS GAINED" if last_delta > 0 else
                                 "RANKED POINTS LOST" if last_delta < 0 else "NO RP CHANGE")
        color = tier_color(r.tier)
        if r.next_rp:
            into, size = s.current_rp - r.start_rp, r.next_rp - r.start_rp
            set_bar(self.bar, r.fraction, "", color)
            self.left.setText(f"{into:,} RP")
            self.right.setText(f"{size:,} RP")
            nt, nd = split_label(r.next_label)
            self.nxt.setPixmap(badge_pixmap(nt, nd, 84))
            self.to_next.setText(f"<span style='color:{color};font-size:18px;font-weight:600'>"
                                 f"{r.next_rp - s.current_rp:,} RP</span> &#9654; {r.next_label.upper()}")
        else:
            set_bar(self.bar, 1.0, "", color)
            self.left.setText(f"{s.current_rp - r.start_rp:,} RP into Master")
            self.right.setText("")
            self.nxt.clear()
            self.to_next.setText("TOP RANK")


def _ago(minutes: int) -> str:
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    return f"{minutes // 60}h {minutes % 60:02d}m ago"


def _span(minutes: int) -> str:
    return f"{minutes} min" if minutes < 60 else f"{minutes // 60}h {minutes % 60:02d}m"


class SessionPanel(QFrame):
    """The session you are playing now (or the last one), and the goal for it.
    Sessions start and stop on their own; the button only forces a fresh one."""
    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(4)
        top = QHBoxLayout()
        self.title = QLabel("SESSION")
        self.title.setObjectName("cardTitle")
        self.status = QLabel("")
        self.status.setObjectName("cardSub")
        self.button = QPushButton("New session")
        self.button.setToolTip("End this session now. The next match you log starts a new one with a new goal.")
        top.addWidget(self.title)
        top.addWidget(self.status, 1)
        top.addWidget(self.button)
        self.headline = QLabel("")
        self.headline.setStyleSheet("font-size:20px;font-weight:600;")
        self.bar = make_bar()
        lay.addLayout(top)
        lay.addWidget(self.headline)
        lay.addWidget(self.bar)

    def set(self, ss):
        goal = f"+{ss.goal:,}"
        usual = f"  -  usual session {fmt_delta(ss.avg_net)}" if ss.avg_net is not None else ""
        if ss.reached:
            self.status.setText("Target reached")
            self.headline.setText("No goal needed")
            self.headline.setStyleSheet("font-size:20px;font-weight:600;color:#2ecc71;")
            set_bar(self.bar, 1.0, "Target reached", "#2ecc71")
            return
        if ss.state == "none":
            self.status.setText("No session yet today. It starts by itself with your next match." + usual)
            self.headline.setText(f"Goal for your first session: {goal}")
            self.headline.setStyleSheet("font-size:20px;font-weight:600;")
            set_bar(self.bar, 0.0, f"0 / {goal}")
        elif ss.state == "live":
            n = ss.count_today
            self.status.setText(f"LIVE  -  session {n} today  -  last match {_ago(ss.minutes_since or 0)}" + usual)
            self.headline.setText(f"{fmt_delta(ss.net)} RP in {ss.matches} match{'es' if ss.matches != 1 else ''}"
                                  f"  -  {_span(ss.last.minutes)}")
            self.headline.setStyleSheet(f"font-size:20px;font-weight:600;color:{rp_color(ss.net)};")
            text = f"{fmt_delta(ss.net)} / {goal}"
            if ss.over > 0:
                text += f"  session goal beaten by +{ss.over:,}"
            set_bar(self.bar, ss.fraction, text, "#2ecc71" if ss.fraction >= 1 else None)
        else:
            last = ss.last
            self.status.setText(f"ENDED  -  stopped {_ago(ss.minutes_since or 0)}  "
                                f"(last match {last.end:%H:%M}, {ss.count_today} session"
                                f"{'s' if ss.count_today != 1 else ''} today)" + usual)
            self.headline.setText(f"Last session {fmt_delta(last.net)} RP in {last.matches} "
                                  f"match{'es' if last.matches != 1 else ''}  -  next goal {goal}")
            self.headline.setStyleSheet("font-size:20px;font-weight:600;")
            set_bar(self.bar, 0.0, f"next session goal {goal}")

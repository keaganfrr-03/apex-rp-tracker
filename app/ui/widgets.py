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


def fill_matches(table, matches, start_rp, limit=None):
    """Newest first. Shows match number of the day, time, RP change and RP after."""
    running, per_day, rows = start_rp, {}, []
    for m in matches:
        running += m.delta
        per_day[m.day] = per_day.get(m.day, 0) + 1
        rows.append((m, per_day[m.day], running))
    rows.reverse()
    if limit:
        rows = rows[:limit]
    table.setRowCount(len(rows))
    for r, (m, n, after) in enumerate(rows):
        cells = [colored_item(m.played_at.strftime("%a %d %b"), align=Qt.AlignLeft),
                 colored_item(f"#{n}  {m.played_at:%H:%M}", align=Qt.AlignLeft),
                 colored_item(fmt_delta(m.delta), rp_color(m.delta)),
                 colored_item(f"{after:,}"),
                 colored_item(m.note, align=Qt.AlignLeft)]
        for c, it in enumerate(cells):
            table.setItem(r, c, it)
        table.item(r, 0).setData(Qt.UserRole, m.id)


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

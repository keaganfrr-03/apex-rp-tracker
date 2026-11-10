import os
from datetime import datetime

from PySide6.QtCore import QDate, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QFormLayout, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox,
                               QPushButton, QSpinBox, QSplitter, QTabWidget, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget, QGridLayout, QHeaderView)

from .. import paths
from ..db import Database
from ..parsing import parse_rp
from ..ranks import target_options, validate_ladder
from ..tracker import Tracker
from .theme import GREEN, STYLE, fmt_delta, rp_color
from .widgets import (CalculatorDialog, Card, EditMatchDialog, RankHero, colored_item, fill_matches, make_bar, make_table,
                      selected_match_id, set_bar)


class Dashboard(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QVBoxLayout(self)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel("Apex RP Tracker")
        title.setStyleSheet("font-size:20px;font-weight:600;")
        self.date_lbl = QLabel("")
        self.date_lbl.setObjectName("cardSub")
        head.addWidget(title)
        head.addStretch()
        head.addWidget(self.date_lbl)
        stream = QPushButton("Stream mode")
        stream.clicked.connect(self.win.open_stream)
        head.addWidget(stream)
        root.addLayout(head)

        self.hero = RankHero()
        root.addWidget(self.hero)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.c_rp, self.c_today = Card("CURRENT RP"), Card("TODAY")
        self.c_goal, self.c_avg, self.c_target = Card("DAILY GOAL"), Card("USUAL / DAY"), Card("TARGET")
        for i, c in enumerate((self.c_rp, self.c_today, self.c_goal, self.c_avg, self.c_target)):
            grid.addWidget(c, 0, i)
        root.addLayout(grid)

        self.bar_goal, self.bar_target = make_bar(), make_bar()
        for text, bar in (("Today's goal", self.bar_goal), ("Progress to target", self.bar_target)):
            row = QHBoxLayout()
            lbl = QLabel(text)
            lbl.setFixedWidth(170)
            row.addWidget(lbl)
            row.addWidget(bar)
            root.addLayout(row)

        entry = QHBoxLayout()
        self.delta = QLineEdit()
        self.delta.setPlaceholderText("+125 or -45")
        self.delta.setMinimumWidth(170)
        self.delta.setStyleSheet("font-size:18px;padding:9px 11px;")
        self.delta.returnPressed.connect(self.add)
        self.note = QLineEdit()
        self.note.setPlaceholderText("Note (optional)")
        self.note.returnPressed.connect(self.add)
        add = QPushButton("Add match")
        add.setObjectName("primary")
        add.clicked.connect(self.add)
        undo = QPushButton("Undo last")
        undo.clicked.connect(self.undo)
        calc = QPushButton("Match calculator...")
        calc.clicked.connect(self.calculator)
        sync = QPushButton("Set current RP...")
        sync.clicked.connect(self.sync_rp)
        entry.addWidget(self.delta, 2)
        entry.addWidget(self.note, 2)
        entry.addWidget(add)
        entry.addWidget(undo)
        entry.addWidget(calc)
        entry.addWidget(sync)
        root.addLayout(entry)
        self.err = QLabel("")
        self.err.setStyleSheet("color:#ff5252;")
        root.addWidget(self.err)

        root.addWidget(QLabel("Recent matches"))
        self.table = make_table(["Date", "Match", "RP", "RP after", "Note"])
        self.table.doubleClicked.connect(self.edit_selected)
        root.addWidget(self.table, 1)

    def add(self):
        try:
            d = parse_rp(self.delta.text())
        except ValueError as e:
            self.err.setText(str(e))
            return
        self.err.setText("")
        self.win.tracker.db.add_match(d, self.note.text())
        self.delta.clear()
        self.note.clear()
        self.delta.setFocus()
        self.win.refresh()

    def calculator(self):
        dlg = CalculatorDialog(self, entry_cost=self.win.tracker.snapshot().entry_cost)
        if dlg.exec():
            self.win.tracker.db.add_match(dlg.net(), dlg.note())
            self.win.refresh()

    def undo(self):
        last = self.win.tracker.db.last_match()
        if last is None:
            return
        if QMessageBox.question(self, "Undo last match",
                                f"Delete the last match ({fmt_delta(last.delta)} RP)?") == QMessageBox.Yes:
            self.win.tracker.db.delete_match(last.id)
            self.win.refresh()

    def sync_rp(self):
        cur = self.win.tracker.current_rp()
        v, ok = QInputDialog.getInt(self, "Set current RP",
                                    "Your RP in game right now (history is kept):", cur, 0, 100000)
        if ok:
            self.win.tracker.set_current_rp(v)
            self.win.refresh()

    def edit_selected(self):
        self.win.edit_match(selected_match_id(self.table))

    def refresh(self, s):
        self.date_lbl.setText(s.day.strftime("%A %d %B %Y"))
        self.c_rp.set(f"{s.current_rp:,}", s.rank.label)
        self.c_today.set(fmt_delta(s.today_net), f"{s.today_count} matches today", rp_color(s.today_net))
        g = s.goal
        if g.reached:
            self.c_goal.set("Done", "Target reached", GREEN)
        elif g.beaten and g.next_goal is not None:
            # Gained more than today's goal: the per-day goal drops to the new, lower figure straight away.
            self.c_goal.set(f"+{g.next_goal:,}", f"new goal/day, +{g.over:,} over", GREEN)
        elif g.beaten:
            self.c_goal.set(f"+{g.goal:,}", f"beaten by +{g.over:,} (last day)", GREEN)
        else:
            self.c_goal.set(f"+{g.goal:,}", f"{g.days_left} season days left")
        if s.avg_per_day is None:
            self.c_avg.set("-", "no matches yet")
        else:
            self.c_avg.set(fmt_delta(s.avg_per_day), f"average over {s.avg_days} day{'s' if s.avg_days != 1 else ''}",
                           rp_color(s.avg_per_day))
        self.c_target.set(s.target_label, f"{g.remaining:,} RP to go" if not g.reached else "Reached", None)
        if g.reached:
            bar_text = "Target reached"
        elif g.beaten:
            bar_text = f"{fmt_delta(s.today_net)} / +{g.goal:,}  goal beaten by +{g.over:,}"
        else:
            bar_text = f"{fmt_delta(s.today_net)} / +{g.goal:,}"
        if not g.reached and g.next_goal is not None:
            bar_text += f"   |   tomorrow's goal +{g.next_goal:,}"
        set_bar(self.bar_goal, g.fraction, bar_text, GREEN if g.fraction >= 1 else None)
        last = self.win.tracker.db.last_match()
        self.hero.set(s, last.delta if last else None)
        set_bar(self.bar_target, s.current_rp / s.target_rp if s.target_rp else 1.0,
                f"{s.current_rp:,} / {s.target_rp:,}")
        fill_matches(self.table, self.win.tracker.db.recent_matches(10), s.start_rp)


class History(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QHBoxLayout(self)
        left, right = QVBoxLayout(), QVBoxLayout()
        left.addWidget(QLabel("All matches (double-click to edit)"))
        self.table = make_table(["Date", "Match", "RP", "RP after", "Note"])
        self.table.doubleClicked.connect(self.edit)
        left.addWidget(self.table)
        btns = QHBoxLayout()
        e, d = QPushButton("Edit"), QPushButton("Delete")
        d.setObjectName("danger")
        e.clicked.connect(self.edit)
        d.clicked.connect(self.delete)
        btns.addWidget(e)
        btns.addWidget(d)
        btns.addStretch()
        left.addLayout(btns)
        right.addWidget(QLabel("Daily totals"))
        self.days = make_table(["Day", "Matches", "Net RP"])
        right.addWidget(self.days)
        lw, rw = QWidget(), QWidget()
        lw.setLayout(left)
        rw.setLayout(right)
        sp = QSplitter()
        sp.addWidget(lw)
        sp.addWidget(rw)
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 1)
        root.addWidget(sp)

    def edit(self):
        self.win.edit_match(selected_match_id(self.table))

    def delete(self):
        mid = selected_match_id(self.table)
        if mid is None:
            return
        if QMessageBox.question(self, "Delete match", "Delete the selected match?") == QMessageBox.Yes:
            self.win.tracker.db.delete_match(mid)
            self.win.refresh()

    def refresh(self, s):
        fill_matches(self.table, self.win.tracker.db.recent_matches(), s.start_rp)
        totals = self.win.tracker.db.daily_totals()
        self.days.setRowCount(len(totals))
        for r, (day, n, net) in enumerate(totals):
            self.days.setItem(r, 0, colored_item(day, align=Qt.AlignLeft))
            self.days.setItem(r, 1, colored_item(str(n)))
            self.days.setItem(r, 2, colored_item(fmt_delta(net), rp_color(net)))


class Settings(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.start = QSpinBox()
        self.start.setRange(0, 100000)
        self.start.setToolTip("Your RP right now. Only change this if it does not match the game.")
        self._synced_rp = 0
        self.target = QComboBox()
        self.season_end = QDateEdit()
        self.season_end.setCalendarPopup(True)
        self.season_end.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Current RP (change only if it is wrong)", self.start)
        form.addRow("Target rank", self.target)
        form.addRow("Season end date", self.season_end)
        root.addLayout(form)

        root.addWidget(QLabel("Rank ladder: RP where each division starts, and entry cost per match"))
        tables = QHBoxLayout()
        self.thr = QTableWidget(0, 3)
        self.thr.setHorizontalHeaderLabels(["Division", "Starts at RP", "RP to next"])
        self.cost = QTableWidget(0, 2)
        self.cost.setHorizontalHeaderLabels(["Tier", "Entry cost"])
        for t in (self.thr, self.cost):
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            t.verticalHeader().setVisible(False)
        self.thr.itemChanged.connect(self._recalc_gaps)
        tables.addWidget(self.thr, 3)
        tables.addWidget(self.cost, 2)
        root.addLayout(tables, 1)
        self.verified = QCheckBox("I have checked these numbers against the game")
        self.thr_note = QLineEdit()
        self.thr_note.setPlaceholderText("Where you checked them")
        root.addWidget(self.verified)
        root.addWidget(self.thr_note)

        row = QHBoxLayout()
        save = QPushButton("Save settings")
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        reset = QPushButton("Reset ladder to Season 31 defaults")
        reset.clicked.connect(self.reset)
        bk = QPushButton("Back up now")
        bk.clicked.connect(self.backup)
        op = QPushButton("Open data folder")
        op.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.data_dir()))))
        for b_ in (save, reset, bk, op):
            row.addWidget(b_)
        root.addLayout(row)
        self.msg = QLabel("")
        root.addWidget(self.msg)
        self.load()

    def sync_rp(self, rp):
        """Keep the box equal to the real RP, so saving other settings can never overwrite it."""
        if self.start.hasFocus():
            return
        self.start.blockSignals(True)
        self.start.setValue(int(rp))
        self.start.blockSignals(False)
        self._synced_rp = int(rp)

    def _fill_targets(self, ladder, selected):
        self.target.clear()
        for label, rp in target_options(ladder):
            self.target.addItem(f"{label}  ({rp:,} RP)", label)
        i = self.target.findData(selected)
        self.target.setCurrentIndex(i if i >= 0 else self.target.count() - 1)

    def _fill_ladder(self, ladder):
        self.thr.blockSignals(True)
        self.thr.setRowCount(len(ladder))
        for r, (name, floor) in enumerate(ladder):
            self.thr.setItem(r, 0, colored_item(name, align=Qt.AlignLeft))
            it = QTableWidgetItem(str(floor))
            if r == 0:
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.thr.setItem(r, 1, it)
            self.thr.setItem(r, 2, colored_item(""))
        self.thr.blockSignals(False)
        self._recalc_gaps()

    def _recalc_gaps(self, *_):
        self.thr.blockSignals(True)
        n = self.thr.rowCount()
        for r in range(n):
            gap = "-"
            if r < n - 1:
                try:
                    gap = f"{int(self.thr.item(r + 1, 1).text()) - int(self.thr.item(r, 1).text()):,}"
                except (ValueError, AttributeError):
                    gap = "?"
            self.thr.setItem(r, 2, colored_item(gap))
        self.thr.blockSignals(False)

    def load(self):
        t = self.win.tracker
        self.sync_rp(t.current_rp())
        self.season_end.setDate(QDate(t.season_end.year, t.season_end.month, t.season_end.day))
        self._fill_ladder(t.ladder)
        self._fill_targets(t.ladder, t.db.get_setting("target_label"))
        costs = t.entry_costs
        self.cost.setRowCount(len(costs))
        for r, (name, c) in enumerate(costs.items()):
            self.cost.setItem(r, 0, colored_item(name, align=Qt.AlignLeft))
            self.cost.setItem(r, 1, QTableWidgetItem(str(c)))
        self.verified.setChecked(t.db.get_setting("thresholds_verified") == "1")
        self.thr_note.setText(t.db.get_setting("thresholds_note", ""))

    def _read_ladder(self):
        out = []
        for r in range(self.thr.rowCount()):
            name = self.thr.item(r, 0).text()
            try:
                out.append((name, int(self.thr.item(r, 1).text().replace(",", ""))))
            except ValueError:
                raise ValueError(f"RP for {name} must be a whole number.")
        return out

    def _read_costs(self):
        out = {}
        for r in range(self.cost.rowCount()):
            name = self.cost.item(r, 0).text()
            try:
                out[name] = abs(int(self.cost.item(r, 1).text()))
            except ValueError:
                raise ValueError(f"Entry cost for {name} must be a whole number.")
        return out

    def save(self):
        try:
            ladder = self._read_ladder()
            costs = self._read_costs()
            validate_ladder(ladder)
            t = self.win.tracker
            if self.start.value() != self._synced_rp:      # only touch RP if you actually changed it
                t.set_current_rp(self.start.value())
            t.save_settings(
                start_rp=t.start_rp, season_end=self.season_end.date().toPython(),
                target_label=self.target.currentData() or "", ladder=ladder,
                note=self.thr_note.text(), verified=self.verified.isChecked(),
                entry_costs=costs)
        except ValueError as e:
            QMessageBox.warning(self, "Check the settings", str(e))
            return
        self._fill_targets(ladder, self.target.currentData())
        self.win.tracker.db.set_setting("target_label", self.target.currentData())
        self.msg.setText("Saved.")
        self.win.refresh()

    def reset(self):
        self.win.tracker.reset_thresholds()
        self.load()

    def backup(self):
        p = self.win.tracker.db.backup(self.win.backup_dir)
        self.msg.setText(f"Backup saved: {p}")


class MainWindow(QMainWindow):
    def __init__(self, db_file=None):
        super().__init__()
        self.setWindowTitle("Apex RP Tracker v6")
        self.resize(1040, 900)
        self.setStyleSheet(STYLE)
        self.db = Database(db_file or paths.db_path())
        self.tracker = Tracker(self.db)
        self.backup_dir = paths.backup_dir() if db_file is None else self.db.path.parent / "backups"
        if not self.db.has_backup_today(self.backup_dir):
            self.db.backup(self.backup_dir)

        self.dash, self.hist, self.sett = Dashboard(self), History(self), Settings(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.dash, "Dashboard")
        self.tabs.addTab(self.hist, "History")
        self.tabs.addTab(self.sett, "Settings")
        self.setCentralWidget(self.tabs)

        self.stream = None
        self._day = datetime.now().date()
        self.timer = QTimer(self)             # only wakes up to notice midnight and roll "today" over
        self.timer.timeout.connect(self._tick)
        self.timer.start(30000)
        self.refresh()

    def _tick(self):
        today = datetime.now().date()
        if today != self._day:
            self._day = today
            self.refresh()

    def refresh(self):
        s = self.tracker.snapshot(datetime.now().date())
        self.dash.refresh(s)
        self.hist.refresh(s)
        self.sett.sync_rp(s.current_rp)
        if self.stream is not None:
            self.stream.refresh(s)

    def open_stream(self):
        if self.stream is None:
            from .stream import StreamWindow      # loaded on first use, keeps start-up quick
            self.stream = StreamWindow()
        self.stream.refresh(self.tracker.snapshot(datetime.now().date()))
        self.stream.show()
        self.stream.raise_()

    def edit_match(self, match_id):
        if match_id is None:
            return
        m = next((x for x in self.db.list_matches() if x.id == match_id), None)
        if m is None:
            return
        dlg = EditMatchDialog(m, self)
        if dlg.exec() and dlg.result_values:
            d, note, when = dlg.result_values
            self.db.update_match(match_id, d, note, when)
            self.refresh()

    def closeEvent(self, e):
        if self.stream is not None:
            self.stream.close()
        self.db.close()
        super().closeEvent(e)

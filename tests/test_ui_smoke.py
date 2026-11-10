import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from datetime import datetime

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_add_edit_delete_flow(qapp, tmp_path):
    w = MainWindow(db_file=tmp_path / "ui.db")
    w.tracker.set_current_rp(0)          # new databases start at your real RP; the maths here starts from 0
    d = w.dash
    d.delta.setText("+125"); d.add()
    d.delta.setText("-45"); d.add()
    assert w.tracker.current_rp() == 80
    assert d.c_today.value.text() == "+80"
    assert d.c_rp.value.text() == "80"
    assert d.table.rowCount() == 2
    d.delta.setText("oops"); d.add()
    assert d.err.text() and w.tracker.current_rp() == 80       # bad input rejected
    # colours: positive green, negative red
    top = d.table.item(0, 2)   # newest first: -45
    assert top.text() == "-45" and top.foreground().color().name() == "#ff5252"
    assert d.table.item(1, 2).foreground().color().name() == "#2ecc71"
    # edit + delete
    m = w.db.list_matches()[1]
    w.db.update_match(m.id, -50, "edited", m.played_at)
    w.refresh()
    assert w.tracker.current_rp() == 75
    w.db.delete_match(m.id)
    w.refresh()
    assert w.tracker.current_rp() == 125 and d.table.rowCount() == 1
    assert w.hist.days.rowCount() == 1
    w.sett.backup()
    assert list((tmp_path / "backups").glob("apex_rp_*.db"))
    w.close()


def test_calculator_adds_match(qapp, tmp_path):
    from app.ui.widgets import CalculatorDialog
    w = MainWindow(db_file=tmp_path / "c.db")
    w.tracker.set_current_rp(0)
    dlg = CalculatorDialog()
    for k, v in (("kills", 14), ("assists", 14), ("participation", 7), ("placement", 20), ("entry", 38)):
        dlg.fields[k].setValue(v)
    dlg.place.setText("8")
    assert dlg.net() == 17 and dlg.total.text() == "+17"
    w.db.add_match(dlg.net(), dlg.note())
    w.refresh()
    assert w.tracker.current_rp() == 17 and "#8" in w.db.last_match().note
    assert w.sett.thr.item(12, 0).text() == "Gold IV" and w.sett.thr.item(12, 2).text() == "750"
    assert w.tracker.snapshot().entry_cost == 0     # Rookie tier right now
    w.tracker.set_current_rp(7173)
    assert w.tracker.snapshot().entry_cost == 38 and w.tracker.snapshot().rank.label == "Gold II"
    assert CalculatorDialog(entry_cost=38).fields["entry"].value() == 38
    w.close()


def test_badges_hero_and_stream(qapp, tmp_path, monkeypatch):
    from app.ui import badges
    monkeypatch.setenv("APEX_RP_DATA_DIR", str(tmp_path / "data"))
    badges.clear_cache()
    for tier, div in (("Rookie", "IV"), ("Gold", "II"), ("Platinum", "I"), ("Diamond", "III"), ("Master", "")):
        pm = badges.badge_pixmap(tier, div, 96)
        assert pm.width() == 96 and not pm.isNull()
    # a user-supplied PNG is used instead of the drawn badge
    (tmp_path / "data" / "badges").mkdir(parents=True)
    drawn = badges.badge_pixmap("Gold", "II", 64).toImage()
    custom = badges.QPixmap(64, 64)
    custom.fill(badges.QColor("#ff00ff"))
    custom.save(str(tmp_path / "data" / "badges" / "gold_ii.png"))
    badges.clear_cache()
    assert badges.badge_pixmap("Gold", "II", 64).toImage().pixelColor(32, 32).name() == "#ff00ff"
    badges.clear_cache()

    w = MainWindow(db_file=tmp_path / "v4.db")
    w.tracker.set_current_rp(7173)       # Gold II, 173 into a 750 RP division
    w.db.add_match(-33)
    w.open_stream()
    w.refresh()
    assert w.dash.hero.left.text() == "140 RP" and w.dash.hero.right.text() == "750 RP"
    assert "610" in w.dash.hero.to_next.text() and "GOLD I" in w.dash.hero.to_next.text()
    assert w.dash.hero.big.text() == "-33"
    assert w.stream.today.value.text() == "-33" and "GOLD II" in w.stream.cur.sub.text()
    assert w.stream.windowFlags() & badges.Qt.WindowStaysOnTopHint
    w.stream.resize(400, 80)
    w.stream.set_flag(badges.Qt.FramelessWindowHint, True)
    w.close()


def test_default_screen_matches_the_game_and_has_no_popup(qapp, tmp_path):
    w = MainWindow(db_file=tmp_path / "d.db")
    assert w.tracker.current_rp() == 7140
    assert w.dash.c_rp.value.text() == "7,140" and w.dash.c_rp.sub.text() == "Gold II"
    assert w.dash.hero.left.text() == "140 RP" and w.dash.hero.right.text() == "750 RP"
    assert "610" in w.dash.hero.to_next.text() and "GOLD I" in w.dash.hero.to_next.text()
    assert not hasattr(w.dash, "warn") and not hasattr(w, "_first_run")
    assert w.stream is None                       # stream window is only created when opened
    w.close()


def test_saving_settings_never_overwrites_your_rp(qapp, tmp_path):
    w = MainWindow(db_file=tmp_path / "s.db")
    w.tracker.set_current_rp(9000)                # e.g. the dashboard's "Set current RP..." button
    w.db.add_match(50)
    w.refresh()
    assert w.sett.start.value() == 9050            # settings box follows the real RP
    w.sett.save()                                  # saving other settings must not touch it
    assert w.tracker.current_rp() == 9050
    w.sett.start.setValue(9100)                    # only a deliberate change moves it
    w.sett.save()
    assert w.tracker.current_rp() == 9100 and w.db.match_count() == 1
    w.close()

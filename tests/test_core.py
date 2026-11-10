from datetime import date, datetime, timedelta

import pytest

from app.db import Database
from app.goals import daily_goal
from app.parsing import parse_rp
from app.ranks import DEFAULT_ENTRY_COSTS, DEFAULT_LADDER, rank_for, target_options, tier_of, validate_ladder
from app.tracker import Tracker


@pytest.fixture
def tr(tmp_path):
    db = Database(tmp_path / "t.db")
    t = Tracker(db)
    yield t
    db.close()


def test_parse():
    assert parse_rp("+125") == 125
    assert parse_rp("-45") == -45
    assert parse_rp(" 60 ") == 60
    assert parse_rp("\u221230") == -30
    for bad in ["", "abc", "+-5", "12.5", "100000"]:
        with pytest.raises(ValueError):
            parse_rp(bad)


def test_ranks_season_31():
    assert rank_for(0).label == "Rookie IV"
    assert rank_for(999).label == "Rookie I"
    assert rank_for(5499).label == "Silver I"
    assert rank_for(5500).label == "Gold IV"
    assert rank_for(6250).label == "Gold III"
    assert rank_for(8500).label == "Platinum IV"
    assert rank_for(10999).label == "Platinum II"        # uneven: II is 10,000-10,999
    assert rank_for(11000).label == "Platinum I"
    assert rank_for(12000).label == "Diamond IV"
    assert rank_for(16000).label == "Master" and rank_for(99999).label == "Master"
    assert rank_for(-50).label == "Rookie IV"
    r = rank_for(5500 + 375)
    assert r.label == "Gold IV" and r.next_rp == 6250 and 0.49 < r.fraction < 0.51
    # Gold divisions are 750 RP: 173 into a division leaves 577
    g = rank_for(7000 + 173)
    assert g.label == "Gold II" and g.next_rp - 7000 - 173 == 577
    assert dict(target_options())["Diamond IV"] == 12000
    assert tier_of("Platinum II") == "Platinum" and tier_of("Master") == "Master"
    assert DEFAULT_ENTRY_COSTS["Gold"] == 38


def test_ladder_validation():
    validate_ladder(DEFAULT_LADDER)
    with pytest.raises(ValueError):
        validate_ladder([("A", 5), ("B", 10)])
    with pytest.raises(ValueError):
        validate_ladder([("A", 0), ("B", 10), ("C", 10)])


def test_goal_is_stable_through_the_day():
    today = date(2026, 11, 10)
    end = today + timedelta(days=9)  # 10 days left including today
    g0 = daily_goal(1000, 0, 2000, end, today)
    assert g0.goal == 100 and g0.days_left == 10
    g1 = daily_goal(1060, 60, 2000, end, today)   # gained 60 today
    assert g1.goal == 100 and abs(g1.fraction - 0.6) < 1e-9
    assert daily_goal(2000, 0, 2000, end, today).reached
    assert daily_goal(1000, 0, 2000, today - timedelta(days=3), today).days_left == 1


def test_matches_edit_delete_and_totals(tr):
    db = tr.db
    d1 = datetime(2026, 11, 9, 23, 50)
    d2 = datetime(2026, 11, 10, 0, 5)
    a = db.add_match(125, when=d1)
    b = db.add_match(-45, "bad drop", when=d2)
    c = db.add_match(60, when=d2 + timedelta(minutes=30))
    assert db.day_total("2026-11-09") == (125, 1)
    assert db.day_total("2026-11-10") == (15, 2)
    assert db.daily_totals() == [("2026-11-10", 2, 15), ("2026-11-09", 1, 125)]
    db.update_match(b, -50, "edited", d2)
    assert db.day_total("2026-11-10") == (10, 2)
    db.delete_match(c)
    assert db.day_total("2026-11-10") == (-50, 1)
    assert db.total_delta() == 75
    # moving an entry to another time moves it to that day
    db.update_match(a, 125, "", d2)
    assert db.day_total("2026-11-09") == (0, 0)


def test_snapshot_and_midnight_rollover(tr):
    tr.save_settings(start_rp=9000, season_end=date(2026, 12, 1), target_label="Diamond IV",
                     ladder=DEFAULT_LADDER, note="x", verified=True)
    tr.db.add_match(200, when=datetime(2026, 11, 9, 22, 0))
    s_day1 = tr.snapshot(date(2026, 11, 9))
    assert s_day1.current_rp == 9200 and s_day1.today_net == 200
    s_day2 = tr.snapshot(date(2026, 11, 10))       # next day: today resets, RP kept
    assert s_day2.current_rp == 9200 and s_day2.today_net == 0 and s_day2.today_count == 0
    assert tr.db.daily_totals()[0] == ("2026-11-09", 1, 200)  # previous total preserved


def test_set_current_rp_keeps_history(tr):
    tr.db.add_match(100)
    tr.set_current_rp(5000)
    assert tr.current_rp() == 5000 and tr.db.total_delta() == 100


def test_backup(tr, tmp_path):
    tr.db.add_match(50)
    p = tr.db.backup(tmp_path / "bk")
    assert p.exists()
    copy = Database(p)
    assert copy.total_delta() == 50
    copy.close()
    assert tr.db.has_backup_today(tmp_path / "bk")

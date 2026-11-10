from datetime import date, datetime, timedelta

import pytest

from app.db import Database
from app.goals import average_gain, daily_goal, project_finish, session_goal
from app.parsing import parse_rp
from app.ranks import DEFAULT_ENTRY_COSTS, DEFAULT_LADDER, rank_for, target_options, tier_of, validate_ladder
from app.sessions import current_session, split_sessions
from app.tracker import DEFAULT_START_RP, Tracker


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


def test_new_database_starts_at_the_rp_from_the_screenshot(tr):
    # Gold II, 307 RP into a 750 RP division, 443 RP to Gold I
    assert DEFAULT_START_RP == 7307 and tr.current_rp() == 7307
    r = tr.snapshot().rank
    assert r.label == "Gold II" and r.next_label == "Gold I"
    assert tr.current_rp() - r.start_rp == 307 and r.next_rp - r.start_rp == 750
    assert r.next_rp - tr.current_rp() == 443
    assert tr.db.get_setting("setup_done") == "1"          # no welcome screen


def test_rp_survives_closing_and_reopening(tmp_path):
    path = tmp_path / "keep.db"
    db = Database(path)
    t = Tracker(db)
    t.db.add_match(-33)
    t.set_current_rp(8123)
    db.close()
    db2 = Database(path)
    t2 = Tracker(db2)                      # must not re-seed or reset anything
    assert t2.current_rp() == 8123 and db2.match_count() == 1
    db2.close()


def test_v4_database_migration(tmp_path):
    def v4_db(name, start, matches=0):
        db = Database(tmp_path / name)     # a v4 database has no "seeded_v5" / "seeded_v6" key
        db.set_setting("start_rp", start)
        for _ in range(matches):
            db.add_match(10)
        return db

    never_filled = v4_db("a.db", 0)
    assert Tracker(never_filled).current_rp() == 7307            # untouched -> gets your RP once

    entered = v4_db("b.db", 5000)
    assert Tracker(entered).current_rp() == 7307                 # v6: your RP is set to 7,307 once

    used = v4_db("c.db", 0, matches=3)
    assert Tracker(used).current_rp() == 7307                    # history kept, total set to 7,307
    assert used.match_count() == 3 and used.total_delta() == 30

    never_filled.set_setting("start_rp", 0)
    assert Tracker(never_filled).current_rp() == 0               # seeds only once, never again
    entered.set_setting("start_rp", 5000)
    assert Tracker(entered).current_rp() == 5000                 # your own number is not replaced again
    for d in (never_filled, entered, used):
        d.close()


def test_recent_matches_numbers_and_running_total(tr):
    db = tr.db
    t0 = datetime(2026, 11, 9, 20, 0)
    plan = [(0, 100), (30, -40), (60 * 5, 25), (60 * 24, 70), (60 * 24 + 5, -33)]
    for minutes, delta in plan:
        db.add_match(delta, f"m{delta}", when=t0 + timedelta(minutes=minutes))
    rows = db.recent_matches()
    assert [m.delta for m, _, _ in rows] == [-33, 70, 25, -40, 100]          # newest first
    # 9 Nov: +100, -40   10 Nov: +25, +70, -33   (numbered within their own day)
    assert [n for _, n, _ in rows] == [3, 2, 1, 2, 1]
    assert [run for _, _, run in rows] == [122, 155, 85, 60, 100]            # running total after each
    assert [m.delta for m, _, _ in db.recent_matches(2)] == [-33, 70]
    assert db.match_count() == 5


def test_beating_the_goal_lowers_the_goal_per_day():
    today = date(2026, 11, 10)
    end = today + timedelta(days=9)                # 10 days left including today
    g0 = daily_goal(1000, 0, 2000, end, today)
    assert g0.goal == 100 and g0.over == 0 and not g0.beaten
    assert g0.next_goal == 112                     # 1000 left / 9 days, rounded up
    g1 = daily_goal(1100, 100, 2000, end, today)   # exactly on goal: not beaten yet
    assert g1.goal == 100 and g1.over == 0 and g1.next_goal == 100
    g2 = daily_goal(1250, 250, 2000, end, today)   # 150 more than the goal
    assert g2.goal == 100 and g2.over == 150 and g2.beaten
    assert g2.next_goal == 84 and g2.next_goal < g0.next_goal      # 750 left / 9 days
    # what the card promises for tomorrow is what the dashboard shows after midnight
    tomorrow = daily_goal(1250, 0, 2000, end, today + timedelta(days=1))
    assert tomorrow.goal == g2.next_goal
    last = daily_goal(1250, 250, 2000, today, today)               # last season day: no "tomorrow"
    assert last.next_goal is None and last.goal == 1000


def test_usual_gain_per_day_follows_big_days(tr):
    assert average_gain([]) is None
    assert average_gain([("2026-11-10", 3, 200), ("2026-11-09", 2, 100)]) == 150
    assert tr.snapshot().avg_per_day is None
    tr.db.add_match(100, when=datetime(2026, 11, 9, 20, 0))
    tr.db.add_match(100, when=datetime(2026, 11, 10, 20, 0))
    s = tr.snapshot(date(2026, 11, 10))
    assert s.avg_per_day == 100 and s.avg_days == 2
    tr.db.add_match(300, when=datetime(2026, 11, 10, 21, 0))       # a big day
    assert tr.snapshot(date(2026, 11, 10)).avg_per_day == 250


class _M:
    def __init__(self, t, delta):
        self.played_at, self.delta = t, delta


def _t(h, m, day=10):
    return datetime(2026, 11, day, h, m)


def test_sessions_split_by_gap_day_and_manual_break():
    ms = [_M(_t(13, 34), 109), _M(_t(13, 35), 45), _M(_t(14, 2), -10), _M(_t(15, 30), 20)]
    sess = split_sessions(ms, 45)
    assert [(x.matches, x.net) for x in sess] == [(3, 144), (1, 20)]   # 88 minute break starts a new one
    assert sess[0].minutes == 28 and sess[0].day == "2026-11-10"
    assert len(split_sessions(ms, 120)) == 1                           # a longer allowed gap keeps it as one
    assert len(split_sessions(ms, 120, breaks=[_t(14, 10)])) == 2     # "New session" button
    night = [_M(_t(23, 50, 9), 10), _M(_t(0, 10), 10)]
    assert len(split_sessions(night, 45)) == 2                         # midnight always starts a new session
    assert split_sessions([], 45) == []


def test_session_live_then_ended_when_you_stop():
    sess = split_sessions([_M(_t(14, 0), 10), _M(_t(14, 20), 10)], 45)
    s, live = current_session(sess, _t(14, 40), 45)
    assert live and s.matches == 2
    s, live = current_session(sess, _t(15, 6), 45)                     # more than 45 minutes of nothing
    assert not live and s is not None
    s, live = current_session(sess, _t(14, 40), 45, breaks=[_t(14, 30)])
    assert not live                                                    # ended by hand
    assert current_session([], _t(14, 40), 45) == (None, False)
    assert current_session(sess, _t(14, 40, day=11), 45)[0] is None    # nothing played "today" yet


def test_session_goal_is_smaller_when_you_already_played():
    assert session_goal(500, 0, 7000, 12000, 10) == 500        # first session of the day: the day's goal
    assert session_goal(500, 150, 7150, 12000, 10) == 350      # second session: what is left of it
    assert session_goal(500, 550, 7550, 12000, 10) == 445      # day goal done: fresh goal, smaller than 500
    assert session_goal(0, 0, 12000, 12000, 10) == 0


def test_tracker_gives_each_session_its_own_goal(tr):
    today = date(2026, 11, 10)
    tr.save_settings(start_rp=7000, season_end=today + timedelta(days=9), target_label="Diamond IV",
                     ladder=DEFAULT_LADDER, note="", verified=True)
    tr.set_current_rp(7000)
    s = tr.snapshot(today, _t(12, 0)).session
    assert s.state == "none" and s.goal == 500 and s.count_today == 0
    tr.db.add_match(100, when=_t(13, 0))
    tr.db.add_match(50, when=_t(13, 20))
    s = tr.snapshot(today, _t(13, 30)).session
    assert s.state == "live" and s.net == 150 and s.matches == 2 and s.goal == 500
    assert abs(s.fraction - 0.3) < 1e-9 and s.over == 0
    s = tr.snapshot(today, _t(15, 0)).session                  # you stopped playing
    assert s.state == "ended" and s.net == 0 and s.last.net == 150 and s.minutes_since == 100
    assert s.goal == 350                                       # next session: smaller, 150 already done
    tr.db.add_match(400, when=_t(15, 10))                      # play again later: a new session by itself
    snap = tr.snapshot(today, _t(15, 20))
    s = snap.session
    assert s.state == "live" and s.count_today == 2 and s.net == 400 and s.goal == 350 and s.over == 50
    assert snap.goal.beaten
    s = tr.snapshot(today, _t(17, 0)).session
    assert s.state == "ended" and s.goal == 445                # day goal done: a fresh, smaller goal
    tr.new_session(_t(17, 30))                                 # pressing "New session" also ends a live one
    tr.db.add_match(10, when=_t(17, 40))
    assert tr.snapshot(today, _t(17, 45)).session.count_today == 3
    tr.new_session(_t(17, 50))
    assert tr.snapshot(today, _t(17, 55)).session.state == "ended"
    assert [x.matches for x in tr.all_sessions()] == [2, 1, 1]
    tr.set_session_gap(10)
    assert tr.session_gap_min == 10


def test_every_change_is_saved_and_journaled(tr):
    mid = tr.db.add_match(65, "win", when=_t(14, 38))
    tr.db.update_match(mid, 60, "fixed", _t(14, 38))
    tr.set_current_rp(7331)
    tr.db.delete_match(mid)
    assert tr.db.disk_total() == tr.db.total_delta() == 0              # a separate connection sees it
    lines = tr.db.journal_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("time,action")
    assert [x.split(",")[1] for x in lines[1:]] == ["set_rp", "add", "edit", "set_rp", "delete"]
    assert lines[-1].endswith(",7271")                         # 7,331 minus the deleted +60
    tr.db.journal_path.unlink()
    tr.db.add_match(5)                                                  # journal is recreated; never blocks saving
    assert tr.db.journal_path.exists() and tr.db.total_delta() == 5


def test_projection_and_usual_session(tr):
    today = date(2026, 11, 10)
    p = project_finish(7000, 12000, 200, today, today + timedelta(days=60))
    assert p.days_needed == 25 and p.finish == today + timedelta(days=25) and p.days_early == 35
    late = project_finish(7000, 12000, 50, today, today + timedelta(days=60))
    assert late.days_needed == 100 and late.days_early == -40
    assert project_finish(7000, 12000, None, today, today) is None
    assert project_finish(7000, 12000, -20, today, today) is None
    assert project_finish(12000, 12000, 100, today, today) is None
    tr.save_settings(start_rp=7000, season_end=today + timedelta(days=60), target_label="Diamond IV",
                     ladder=DEFAULT_LADDER, note="", verified=True)
    tr.set_current_rp(7000)
    assert tr.snapshot(today, _t(12, 0)).projection is None and tr.snapshot(today, _t(12, 0)).session.avg_net is None
    tr.db.add_match(100, when=_t(13, 0))
    tr.db.add_match(50, when=_t(15, 0))                          # second session
    snap = tr.snapshot(today, _t(15, 5))
    assert snap.session.avg_net == 75 and snap.avg_per_day == 150
    assert snap.projection.days_needed == 33                     # 4,850 left at +150/day = 32.3 days

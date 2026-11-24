from datetime import date, timedelta

import pytest

from src.ingest.collect import collection_window
from src.note.coverage import coverage_caveat
from src.store.models import CollectionRunRecord

GAP = "partial, store feed had gaps"
WINDOW = ("2026-09-07", "2026-11-29")
FULL_BACKFILL = ("backfill", "2026-08-31", "2026-11-22")
SIX_HOURS = "T06:00:00+00:00"
EVENING = "T20:30:00+00:00"


class Runs:
    def __init__(self):
        self.records = []

    def add(self, mode, window_start, window_end, started=None, gaps=0, status="ok", covered_start=None, limit_hit=False):
        clean = not gaps and not limit_hit
        self.records.append(CollectionRunRecord(
            collection_id=len(self.records) + 1, platform="app_store", mode=mode, window_start=window_start,
            window_end=window_end, status=status, started_at=started or window_end + EVENING,
            covered_start=window_start if clean else covered_start, feed_gaps=gaps,
            source_limit_hit=int(gaps > 0 or limit_hit)))
        return self

    def daily(self, day, **kw):
        return self.add("daily", *collection_window("daily", date.fromisoformat(day), 12), **kw)

    def caveat(self, window=WINDOW):
        return coverage_caveat(self.records, *window, reviews=10)


def _backfilled():
    return Runs().add(*FULL_BACKFILL)


def test_clean_daily_runs_after_a_gap_clear_it_together():
    runs = _backfilled().daily("2026-11-23").daily("2026-11-24", gaps=10)
    assert runs.caveat() == GAP
    assert runs.daily("2026-11-25").caveat() is None


def test_first_clean_run_clears_days_only_after_they_ended():
    runs = _backfilled().daily("2026-11-24", gaps=10)
    assert runs.caveat() == GAP
    runs.daily("2026-11-25")
    assert runs.caveat(("2026-09-07", "2026-11-22")) == GAP
    assert runs.caveat(("2026-09-07", "2026-11-21")) is None


def test_a_day_collected_while_it_was_still_running_is_not_complete():
    runs = Runs().add("backfill", "2026-08-31", "2026-11-24", started="2026-11-24" + SIX_HOURS)
    runs.daily("2026-11-25", gaps=3)
    assert runs.caveat(("2026-09-07", "2026-11-23")) is None
    assert runs.caveat(("2026-09-07", "2026-11-24")) == GAP


def test_clean_rerun_on_the_same_day_clears_the_gap():
    runs = Runs().add("backfill", "2026-08-31", "2026-11-23").daily("2026-11-24", gaps=10, started="2026-11-24" + SIX_HOURS)
    assert runs.caveat() == GAP
    assert runs.daily("2026-11-24").caveat() is None


def test_partial_rerun_leaves_the_uncollected_days():
    runs = _backfilled().daily("2026-11-25", gaps=2).add("daily", "2026-11-24", "2026-11-26")
    assert runs.caveat() == GAP
    assert runs.caveat(("2026-11-24", "2026-11-30")) is None
    runs.add("reconcile", "2026-11-23", "2026-11-23", started="2026-12-01" + EVENING)
    assert runs.caveat() is None


def test_repeated_gaps_stay_flagged():
    runs = _backfilled()
    for day in ("2026-11-23", "2026-11-24", "2026-11-25"):
        runs.daily(day, gaps=1)
    assert runs.caveat() == GAP
    runs.daily("2026-11-26")
    assert runs.caveat(("2026-09-07", "2026-11-23")) == GAP
    assert runs.caveat(("2026-11-24", "2026-11-29")) is None


def test_gap_run_never_counts_as_a_recollection():
    runs = _backfilled().daily("2026-11-23", gaps=1).daily("2026-11-24", gaps=1, covered_start="2026-11-20")
    assert runs.caveat(("2026-09-07", "2026-11-23")) == GAP


@pytest.mark.parametrize("status", ["failed", "skipped_disabled"])
def test_unfinished_run_never_counts_as_a_recollection(status):
    runs = _backfilled().daily("2026-11-24", gaps=1).daily("2026-11-25", status=status).daily("2026-11-30")
    assert runs.caveat(("2026-11-23", "2026-11-24")) == GAP


def test_gap_days_outside_the_note_window_do_not_matter():
    runs = _backfilled().daily("2026-11-24", gaps=10)
    assert runs.caveat(("2026-08-31", "2026-11-21")) is None
    assert runs.caveat(("2026-11-25", "2026-11-29")) is None
    assert runs.caveat(("2026-11-24", "2026-11-29")) == GAP


def test_first_day_of_a_truncated_run_is_not_complete():
    runs = Runs().add("backfill", "2026-08-31", "2026-11-23", limit_hit=True, covered_start="2026-11-22")
    runs.add("daily", "2026-11-22", "2026-11-22", gaps=1)
    assert runs.caveat(("2026-11-22", "2026-11-22")) == GAP
    later = Runs().add("backfill", "2026-08-31", "2026-11-23", limit_hit=True, covered_start="2026-11-21")
    later.add("daily", "2026-11-22", "2026-11-22", gaps=1)
    assert later.caveat(("2026-11-22", "2026-11-22")) is None


def test_gap_backfill_is_not_cleared_by_short_daily_runs():
    runs = Runs().add(*FULL_BACKFILL, gaps=4, covered_start="2026-10-02")
    for offset in range(7):
        runs.daily((date(2026, 11, 22) + timedelta(days=offset)).isoformat())
    assert runs.caveat() == GAP


def test_steady_daily_runs_recover_from_one_bad_day_every_time():
    for bad in range(14):
        runs = _backfilled()
        for offset in range(16):
            day = (date(2026, 11, 23) + timedelta(days=offset)).isoformat()
            runs.daily(day, gaps=10 if offset == bad else 0)
        assert runs.caveat(("2026-09-07", "2026-12-08")) is None, bad

import os

import pytest
from fastapi.testclient import TestClient

from src.api.app import RUN_HISTORY_LIMIT, create_app
from src.api.auth import OperatorAuth
from src.config import PROJECT_ROOT, outputs_root
from src.pipeline import run_full_pipeline
from src.registry.dispatch import GitHubDispatcher
from src.registry.service import RegistryService
from src.store.factory import postgres_store, sqlite_store
from src.store.models import AppRecord
from tests.test_phase7_store import BACKENDS, POSTGRES_DSN_ENV, _fresh_postgres_dsn
from tests.test_phase9_registry import _resolver
from tests.test_pulse_status import _theme

WEEK = "2026-11-09"
CSV = PROJECT_ROOT / "tests" / "fixtures" / "reviews_baseline.csv"


@pytest.fixture
def groww(pulse_store):
    return pulse_store.for_app("groww")


@pytest.fixture
def api(pulse_store):
    service = RegistryService(pulse_store, _resolver(), GitHubDispatcher(None, None))
    return TestClient(create_app(service, OperatorAuth(None, frozenset()), outputs_root(), []))


def test_history_lists_every_theme_and_the_same_summary_as_the_week(groww, api):
    run_full_pipeline(groww, WEEK, csv_path=CSV, dry_run=True)
    listed = api.get("/apps/groww/pulses").json()["pulses"][0]
    stored = groww.get_themes(groww.get_pulse_week(WEEK)["run_id"])
    assert [t["label"] for t in listed["themes"]] == [t.label for t in stored]
    assert sum(t["is_top3"] for t in listed["themes"]) == 3
    week = api.get(f"/apps/groww/pulses/{WEEK}").json()
    assert {k: week[k] for k in listed} == listed


def test_week_and_health_count_reviews_per_store_with_the_notes_caveat(groww, api):
    run_full_pipeline(groww, WEEK, csv_path=CSV, dry_run=True)
    week = api.get(f"/apps/groww/pulses/{WEEK}").json()
    play = groww.platform_counts(week["window_start"], week["window_end"])["play_store"]
    assert week["stores"] == [
        {"platform": "play_store", "reviews": play, "caveat": None},
        {"platform": "app_store", "reviews": 0, "caveat": "not collected yet"},
    ]
    assert api.get("/apps/groww/health").json()["stores"] == week["stores"]


def test_health_has_no_store_counts_before_the_first_pulse(api):
    assert api.get("/apps/groww/health").json()["stores"] == []


@pytest.mark.parametrize("coverage, short", [(7.9, True), (8.0, False)])
def test_week_says_when_its_coverage_is_short(groww, api, coverage, short):
    groww.save_theme_run("r1", WEEK, "2026-08-24", "2026-11-15", 5, 5, 3.0, coverage, [_theme("t1")])
    assert api.get(f"/apps/groww/pulses/{WEEK}").json()["short_coverage"] is short


def test_health_lists_recent_runs_newest_first(groww, api):
    for day in range(1, RUN_HISTORY_LIMIT + 3):
        run = groww.start_collection("play_store", "daily", f"2026-11-{day:02d}", f"2026-11-{day:02d}")
        groww.finish_collection(run, "ok", fetched=day)
    runs = api.get("/apps/groww/health").json()["runs"]
    assert [r["fetched"] for r in runs] == list(range(RUN_HISTORY_LIMIT + 2, 2, -1))


def test_health_keeps_another_apps_runs_out(pulse_store, groww, api):
    pulse_store.insert_app(AppRecord("other", "Other", "active", play_package_id="com.other.app"))
    groww.start_collection("play_store", "daily", "2026-11-01", "2026-11-01")
    assert len(api.get("/apps/groww/health").json()["runs"]) == 1
    assert api.get("/apps/other/health").json()["runs"] == []


READ_PATHS = ("/apps", "/apps/groww/pulses", f"/apps/groww/pulses/{WEEK}", "/apps/groww/health", "/apps/nope/health")


@pytest.mark.parametrize("path", READ_PATHS)
def test_read_route_opens_one_connection(pulse_store, groww, api, monkeypatch, path):
    groww.save_theme_run("r1", WEEK, "2026-08-24", "2026-11-15", 5, 5, 3.0, 12.0, [_theme("t1")])
    opened = []
    connect = pulse_store.connector._connect
    monkeypatch.setattr(pulse_store.connector, "_connect", lambda: opened.append(path) or connect())
    assert api.get(path).status_code in (200, 404)
    assert opened == [path]


@pytest.fixture(params=BACKENDS)
def any_store(request, tmp_path):
    if request.param == "sqlite":
        return sqlite_store(tmp_path / "reading.db")
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    return postgres_store(_fresh_postgres_dsn())


def test_writing_while_reading_is_refused(any_store):
    with pytest.raises(Exception, match="read-?only"):
        with any_store.reading():
            any_store.rename_app("groww", "Changed")
    assert any_store.get_app("groww").display_name == "Groww"
    any_store.rename_app("groww", "Changed")
    assert any_store.get_app("groww").display_name == "Changed"


def test_reading_inside_reading_keeps_the_outer_connection(any_store):
    with any_store.reading():
        with any_store.reading():
            any_store.get_app("groww")
        assert any_store.get_app("groww").app_key == "groww"

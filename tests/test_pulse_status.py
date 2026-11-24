import os

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.auth import OperatorAuth
from src.config import PROJECT_ROOT, outputs_root
from src.mcp.publisher import PulsePublisher
from src.pipeline import run_full_pipeline, run_themes_stage
from src.registry.dispatch import GitHubDispatcher
from src.registry.service import RegistryService
from src.store.factory import postgres_store, sqlite_store
from src.store.retention import purge_retention
from tests.conftest import TEST_RECIPIENT
from tests.test_phase7_store import BACKENDS, POSTGRES_DSN_ENV, _fresh_postgres_dsn
from tests.test_phase9_registry import _resolver

WEEK = "2026-11-09"
OLD_WEEK = "2026-11-02"
CSV = PROJECT_ROOT / "tests" / "fixtures" / "reviews_baseline.csv"
CREATE_DRAFT = "GMAIL_CREATE_EMAIL_DRAFT"


@pytest.fixture(params=BACKENDS)
def pulse_store(request, tmp_path):
    if request.param == "sqlite":
        return sqlite_store(tmp_path / "status.db")
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    return postgres_store(_fresh_postgres_dsn())


@pytest.fixture
def groww(pulse_store):
    return pulse_store.for_app("groww")


@pytest.fixture
def api(pulse_store):
    service = RegistryService(pulse_store, _resolver(), GitHubDispatcher(None, None))
    return TestClient(create_app(service, OperatorAuth(None, frozenset()), outputs_root(), []))


def _run(groww, **kw):
    return run_full_pipeline(groww, WEEK, csv_path=CSV, **kw)


def _publish(groww, composio):
    return _run(groww, mcp_client=composio.client())


def _shown(api):
    history = api.get("/apps/groww/pulses").json()["pulses"]
    latest = api.get("/apps/groww/health").json()["latest_pulse"]
    pulse = api.get(f"/apps/groww/pulses/{WEEK}").json()
    assert [p["week_start"] for p in history] == [WEEK]
    return {
        (history[0]["status"], history[0]["published_at"] is not None),
        (latest["status"], latest["published_at"] is not None),
        (pulse["status"], history[0]["published_at"] is not None),
    }


PUBLISHED = {("published", True)}


def _theme(theme_id):
    return {"theme_id": theme_id, "label": theme_id, "description": "d", "review_count": 1, "share_pct": 0.2,
            "avg_rating": 3.0, "is_top3": 1, "neg_share": 0.5, "priority_score": 0.1, "member_review_ids": []}


def _save(store, run_id, week, *theme_ids):
    store.save_theme_run(run_id, week, "2026-08-24", "2026-11-15", 5, 5, 3.0, 12.0, [_theme(t) for t in theme_ids])


def _theme_ids(store, run_id):
    return sorted(t.theme_id for t in store.get_themes(run_id))


def test_published_week_reads_published_everywhere(groww, api, composio):
    assert _publish(groww, composio)["status"] == "published"
    assert _shown(api) == PUBLISHED


def test_dry_run_reads_validated_everywhere(groww, api):
    assert _run(groww, dry_run=True)["status"] == "validated"
    assert _shown(api) == {("validated", False)}


@pytest.mark.parametrize("rerun", [{"dry_run": True}, {"stage_limit": "themes", "dry_run": True}])
def test_unpublished_rerun_does_not_hide_a_published_week(groww, api, composio, rerun):
    _publish(groww, composio)
    _run(groww, **rerun)
    assert _shown(api) == PUBLISHED


def test_standalone_themes_rerun_does_not_hide_a_published_week(groww, api, composio):
    _publish(groww, composio)
    run_themes_stage(groww, WEEK)
    assert _shown(api) == PUBLISHED


def test_standalone_publish_counts_as_published(groww, api, composio):
    _run(groww, dry_run=True)
    PulsePublisher(groww, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)
    assert _shown(api) == PUBLISHED


def test_doc_without_a_draft_is_not_published(groww, api, composio):
    composio.failing_tools.add(CREATE_DRAFT)
    assert _publish(groww, composio)["status"] == "failed"
    assert groww.get_publish_state(WEEK).doc_id
    assert _shown(api) == {("publish_failed", False)}
    composio.failing_tools.clear()
    assert _publish(groww, composio)["status"] == "published"
    assert _shown(api) == PUBLISHED


def test_week_stored_under_two_run_ids_reads_published(groww, api, composio):
    _publish(groww, composio)
    groww.record_run_start("split", WEEK)
    groww.update_run("split", "themes_completed")
    with groww.connector.session() as s:
        s.execute("UPDATE themes SET run_id = 'split' WHERE app_key = 'groww'")
    assert _shown(api) == PUBLISHED


def test_pipeline_run_owns_its_themes(groww, composio):
    result = _publish(groww, composio)
    assert groww.latest_themed_run_for_week(WEEK).run_id == result["run_id"]
    with groww.connector.session() as s:
        assert s.scalar("SELECT COUNT(*) AS n FROM runs WHERE app_key = 'groww'") == 1


def test_saving_themes_keeps_the_run_protected_from_retention(groww):
    _run(groww, stage_limit="ingest", dry_run=True)
    [first, *_] = groww.get_reviews_in_window("2026-08-17", "2026-11-15")
    groww.record_run_start("active", WEEK)
    theme = {**_theme("t1"), "member_review_ids": [first.review_id]}
    groww.save_theme_run("active", WEEK, "2026-08-24", "2026-11-15", 5, 5, 3.0, 12.0, [theme])
    assert purge_retention(groww, "2027-01-01")["active_runs_protected"] == ["active"]
    assert [r.review_id for r in groww.get_reviews_in_window("2026-01-01", "2026-12-31")] == [first.review_id]


def test_rerun_under_a_new_run_id_drops_the_weeks_stale_themes(groww):
    _save(groww, "other-week", OLD_WEEK, "o1", "o2")
    _save(groww, "first", WEEK, "t1", "t2", "t3")
    _save(groww, "second", WEEK, "t1", "t2")
    assert _theme_ids(groww, "first") == []
    assert _theme_ids(groww, "second") == ["t1", "t2"]
    assert _theme_ids(groww, "other-week") == ["o1", "o2"]


def test_published_status_belongs_to_one_week(groww, composio):
    _publish(groww, composio)
    _save(groww, "other-week", OLD_WEEK, "o1")
    assert {row["week_start"]: row["status"] for row in groww.list_pulse_weeks(5)} == {
        WEEK: "published", OLD_WEEK: "themes_completed"}
    assert groww.get_pulse_week(WEEK)["status"] == "published"
    assert groww.get_pulse_week(OLD_WEEK)["status"] == "themes_completed"
    assert groww.get_pulse_week("2026-10-26") is None


def test_week_with_themes_under_two_runs_shows_the_newest_once(groww):
    for run_id in ("older", "newer"):
        _save(groww, run_id, WEEK, f"{run_id}-theme")
    with groww.connector.session() as s:
        s.execute("UPDATE runs SET created_at = '2026-11-16T00:00:00' WHERE app_key = 'groww' AND run_id = 'older'")
        s.execute("INSERT INTO themes (app_key, theme_id, run_id, label, description, review_count, share_pct, avg_rating) "
                  "VALUES ('groww', 'left', 'older', 'L', 'd', 1, 0.1, 3.0)")
    assert [row["run_id"] for row in groww.list_pulse_weeks(5)] == ["newer"]
    assert groww.get_pulse_week(WEEK)["run_id"] == "newer"

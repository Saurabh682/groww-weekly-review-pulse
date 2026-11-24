import csv
import json
import os
import sqlite3
import threading
from datetime import date, datetime, timezone

import pytest
import yaml

from src.config import PROJECT_ROOT, load_pulse_config, outputs_root
from src.ingest.collect import collection_window
from src.mcp.errors import PublishStoppedArchived
from src.mcp.publisher import PulsePublisher
from src.note.engine import build_and_validate_pulse_note
from src.pipeline import run_full_pipeline
from src.registry.dispatch import GitHubDispatcher
from src.registry.service import ListingRequest, RegistryService
from src.scheduler import cli
from src.scheduler.jobs import JobRefused, latest_complete_week, run_job
from src.scheduler.logscan import SECRET_ENV_NAMES, LogScanner
from src.scheduler.plan import CRON_MODES, JOB_MODES, Job, PlanError, plan_jobs, resolve_request
from src.store.factory import open_store, postgres_store, sqlite_store
from src.store.models import AppRecord
from tests.conftest import TEST_RECIPIENT
from tests.test_phase7_store import POSTGRES_DSN_ENV, _fresh_postgres_dsn
from tests.test_phase8_collectors import FakeSource
from tests.test_phase9_registry import _resolver

MONDAY = date(2026, 11, 16)
WORKFLOW_DIR = PROJECT_ROOT / ".github" / "workflows"
PULSE_WORKFLOW = yaml.load((WORKFLOW_DIR / "pulse.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
CI_WORKFLOW = yaml.load((WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
PULSE_TEXT = (WORKFLOW_DIR / "pulse.yml").read_text(encoding="utf-8")
LIVE_NON_ACTIVE = ("pending_backfill", "backfilling", "failed")


def _app(key, status="active"):
    return AppRecord(key, key.title(), status, play_package_id=f"com.example.{key}")


def _baseline(platform="play_store"):
    with open(PROJECT_ROOT / "tests" / "fixtures" / "reviews_baseline.csv", encoding="utf-8") as f:
        return [
            {"platform": platform, "rating": int(r["rating"]), "title": None, "text": r["text"], "date": r["date"],
             "app_version": r["app_version"] or None}
            for r in csv.DictReader(f)
        ]


def _sources(records=None, error=None):
    return {"play_store": FakeSource("play_store", records, error)}


@pytest.fixture
def swiggy(pulse_store):
    pulse_store.insert_app(_app("swiggy", "pending_backfill"))
    return pulse_store.for_app("swiggy")


@pytest.mark.parametrize("cron, mode", [("30 20 * * *", "daily"), ("30 3 * * 1", "pulse"), ("30 21 1 * *", "reconcile")])
def test_SCH_01_cron_to_mode(cron, mode):
    assert resolve_request("schedule", cron, "", "") == (mode, None)


def test_SCH_01_workflow_crons_are_exactly_the_known_crons():
    assert {entry["cron"] for entry in PULSE_WORKFLOW["on"]["schedule"]} == set(CRON_MODES)
    assert tuple(PULSE_WORKFLOW["on"]["workflow_dispatch"]["inputs"]["mode"]["options"]) == JOB_MODES


def test_SCH_01_unknown_cron_and_event_are_refused():
    with pytest.raises(PlanError, match="Unknown cron"):
        resolve_request("schedule", "0 0 * * *", "", "")
    with pytest.raises(PlanError, match="Unsupported event"):
        resolve_request("push", "", "daily", "")
    with pytest.raises(PlanError, match="Unknown mode"):
        resolve_request("workflow_dispatch", "", "everything", "")


def test_SCH_01_scheduled_run_ignores_leftover_inputs():
    assert resolve_request("schedule", "30 20 * * *", "backfill", "groww") == ("daily", None)


@pytest.fixture
def github_env(monkeypatch, tmp_path):
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    for name in ("PULSE_SCHEDULE", "PULSE_MODE", "PULSE_APP_KEY"):
        monkeypatch.setenv(name, "")
    monkeypatch.delenv("PULSE_STORE", raising=False)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    return output


@pytest.mark.parametrize("app_key", ["", "   "])
def test_SCH_02_backfill_needs_app(github_env, monkeypatch, capsys, app_key):
    monkeypatch.setenv("PULSE_MODE", "backfill")
    monkeypatch.setenv("PULSE_APP_KEY", app_key)
    assert cli.run(["plan"]) == cli.EXIT_REFUSED
    assert "mode=backfill needs app_key" in capsys.readouterr().err
    assert not github_env.exists()


def test_SCH_02_unknown_or_wrong_status_app_is_refused():
    apps = [_app("groww"), _app("swiggy", "pending_backfill"), _app("old", "archived")]
    with pytest.raises(PlanError, match="No app registered"):
        plan_jobs("backfill", "nope", apps)
    with pytest.raises(PlanError, match="is pending_backfill"):
        plan_jobs("pulse", "swiggy", apps)
    for mode in JOB_MODES:
        with pytest.raises(PlanError, match="is archived"):
            plan_jobs(mode, "old", apps)


def test_SCH_03_empty_matrix(github_env, monkeypatch):
    open_store().set_app_status("groww", "archived")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("PULSE_SCHEDULE", "30 20 * * *")
    assert cli.run(["plan"]) == cli.EXIT_OK
    assert github_env.read_text(encoding="utf-8") == "jobs=[]\n"
    run = PULSE_WORKFLOW["jobs"]["run"]
    assert (run["needs"], run["if"]) == ("plan", "needs.plan.outputs.jobs != '[]'")


def test_SCH_04_pending_backfill_pickup():
    apps = [_app("swiggy", "pending_backfill"), _app("groww"), _app("stuck", "backfilling"),
            _app("broken", "failed"), _app("old", "archived")]
    assert plan_jobs("daily", None, apps) == [
        Job("groww", "daily"), Job("stuck", "backfill"), Job("swiggy", "backfill"),
    ]


@pytest.mark.parametrize("mode", ["pulse", "reconcile"])
def test_SCH_04_other_modes_take_active_apps_only(mode):
    apps = [_app("groww")] + [_app(s.replace("_", ""), s) for s in LIVE_NON_ACTIVE]
    assert plan_jobs(mode, None, apps) == [Job("groww", mode)]


def test_SCH_04_plan_writes_the_matrix(github_env, monkeypatch, capsys):
    open_store().insert_app(_app("swiggy", "pending_backfill"))
    monkeypatch.setenv("PULSE_MODE", "daily")
    assert cli.run(["plan"]) == cli.EXIT_OK
    jobs = json.loads(github_env.read_text(encoding="utf-8").removeprefix("jobs="))
    assert jobs == [{"app_key": "groww", "mode": "daily"}, {"app_key": "swiggy", "mode": "backfill"}]


@pytest.mark.parametrize("http_status", [401, 404, 422, 500])
def test_SCH_05_dispatch_failure_fallback(pulse_store, http_status):
    dispatcher = GitHubDispatcher("owner/repo", "token", http_post=lambda *_: (http_status, b""))
    service = RegistryService(pulse_store, _resolver(), dispatcher)
    result = service.register(ListingRequest("Swiggy", play_package_id="in.swiggy.android")).to_dict()
    assert result["app"]["status"] == "pending_backfill"
    assert result["backfill_dispatch"]["status"] == "failed"
    assert result["backfill_dispatch"]["message"] == "Backfill is queued for the next daily run."
    assert Job("swiggy", "backfill") in plan_jobs("daily", None, pulse_store.list_apps())


def test_SCH_06_no_overlap_per_app():
    concurrency = PULSE_WORKFLOW["jobs"]["run"]["concurrency"]
    assert concurrency == {"group": "pulse-${{ matrix.app_key }}", "cancel-in-progress": "false"}


def test_SCH_07_failure_isolation_settings():
    strategy = PULSE_WORKFLOW["jobs"]["run"]["strategy"]
    assert (strategy["fail-fast"], strategy["max-parallel"]) == ("false", "2")


def test_SCH_07_one_failed_app_leaves_the_other_green(pulse_store):
    pulse_store.insert_app(_app("swiggy"))
    bad = run_job(pulse_store.for_app("groww"), "daily", MONDAY, sources=_sources(error=RuntimeError("boom")))
    good = run_job(pulse_store.for_app("swiggy"), "daily", MONDAY, sources=_sources([]))
    assert (bad.status, bad.succeeded) == ("failed", False)
    assert (good.status, good.succeeded) == ("ok", True)


REVIEW = "Withdrawals take three days to reach my bank account and nobody answers"


@pytest.mark.parametrize("line, finding", [
    (f"error: could not parse {REVIEW}", "review_text"),
    ("WITHDRAWALS, take three days to... reach", "review_text"),
    ("account owner is someone@example.com", "email"),
    ("header value ck_" + "a" * 20, "secret"),
    ("dsn postgresql://postgres.ref:hunter22@host:5432/postgres", "secret"),
    ("token ghp_" + "a" * 36, "secret"),
])
def test_SCH_08_log_scan(line, finding):
    assert LogScanner(line, {}).findings([REVIEW]) == [finding]


def test_SCH_08_log_scan_catches_configured_secret_values():
    for name in SECRET_ENV_NAMES:
        assert LogScanner("x value-of-secret y", {name: "value-of-secret"}).findings([]) == ["secret"]


def test_SCH_08_short_reviews_are_matched_whole():
    assert LogScanner("note: worst app ever", {}).has_review_text(["Worst app ever!"])
    assert not LogScanner("status ok", {}).has_review_text(["ok", ""])


def test_SCH_08_clean_log_is_shown(tmp_path, capsys):
    open_store()
    log = tmp_path / "job.log"
    log.write_text('{"app_key": "groww", "status": "ok"}\n', encoding="utf-8")
    assert cli.run(["show-log", "--app", "groww", "--file", str(log)]) == cli.EXIT_OK
    assert '"status": "ok"' in capsys.readouterr().out


def test_SCH_08_dirty_log_is_withheld(tmp_path, capsys):
    store = open_store().for_app("groww")
    today = datetime.now(timezone.utc).date().isoformat()
    collected = run_job(store, "daily", datetime.now(timezone.utc).date(), sources=_sources(
        [{"platform": "play_store", "rating": 1, "title": None, "text": REVIEW, "date": today, "app_version": None}]))
    assert collected.status == "ok"
    log = tmp_path / "job.log"
    log.write_text(f"Traceback: {REVIEW}\n", encoding="utf-8")
    assert cli.run(["show-log", "--app", "groww", "--file", str(log)]) == cli.EXIT_LOG_WITHHELD
    captured = capsys.readouterr()
    assert "review_text" in captured.err
    assert "Withdrawals" not in captured.out + captured.err


def test_SCH_08_unreachable_store_withholds_the_log(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("PULSE_STORE", "supabase")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    log = tmp_path / "job.log"
    log.write_text(REVIEW, encoding="utf-8")
    assert cli.run(["show-log", "--app", "groww", "--file", str(log)]) == cli.EXIT_FAILED
    captured = capsys.readouterr()
    assert "Withdrawals" not in captured.out + captured.err


def test_SCH_08_crash_prints_type_and_place_only(capsys, monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError(f"{REVIEW} someone@example.com")

    monkeypatch.setattr("src.scheduler.jobs.collect_app", explode)
    assert cli.run(["run", "--app", "groww", "--mode", "daily"]) == cli.EXIT_FAILED
    err = capsys.readouterr().err
    assert err.startswith("error: RuntimeError at jobs.py:")
    assert "Withdrawals" not in err and "@" not in err


def test_SCH_08_job_output_is_captured_scanned_then_shown():
    steps = PULSE_WORKFLOW["jobs"]["run"]["steps"]
    run_step = next(s for s in steps if s.get("id") == "job")
    show_step = steps[steps.index(run_step) + 1]
    assert run_step["run"].endswith('> "$RUNNER_TEMP/job.log" 2>&1')
    assert "show-log" in show_step["run"]
    assert show_step["if"] == "${{ !cancelled() && steps.job.outcome != 'skipped' }}"


def test_SCH_08_whole_pulse_job_log_passes_the_scan(swiggy, composio, capsys, monkeypatch):
    monkeypatch.setattr(cli, "open_store", lambda: swiggy._store)
    monkeypatch.setattr(cli, "utc_today", lambda: MONDAY)
    monkeypatch.setattr(cli, "run_job", lambda store, mode, today: run_job(
        store, mode, today, sources=_sources(_baseline()), mcp_client=composio.client()))
    assert cli.run(["run", "--app", "swiggy", "--mode", "backfill"]) == cli.EXIT_OK
    log = capsys.readouterr().out
    texts = [r.text for r in swiggy.get_reviews_in_window("2026-01-01", "2026-12-31")]
    assert len(texts) > 100
    assert LogScanner(log, dict(os.environ)).findings(texts) == []
    assert TEST_RECIPIENT not in log and "docs.google.com" not in log


@pytest.mark.parametrize("today, week", [
    (date(2026, 11, 23), date(2026, 11, 16)),
    (date(2026, 11, 29), date(2026, 11, 16)),
    (date(2026, 11, 30), date(2026, 11, 23)),
    (date(2027, 1, 4), date(2026, 12, 28)),
])
def test_SCH_09_week_start(today, week):
    assert latest_complete_week(today) == week
    assert week.weekday() == 0


@pytest.mark.parametrize("today, window", [
    (date(2026, 12, 1), ("2026-11-01", "2026-11-30")),
    (date(2028, 3, 1), ("2028-02-01", "2028-02-29")),
    (date(2027, 3, 1), ("2027-02-01", "2027-02-28")),
    (date(2027, 1, 1), ("2026-12-01", "2026-12-31")),
    (date(2026, 12, 2), ("2026-11-01", "2026-11-30")),
])
def test_SCH_10_reconcile_window(today, window):
    assert collection_window("reconcile", today, 12) == window


def test_SCH_10_reconcile_job_collects_that_month(groww_store):
    source = FakeSource("play_store", [
        {"platform": "play_store", "rating": 4, "title": None, "text": f"Charts load slowly on day {d} of use",
         "date": d, "app_version": None} for d in ("2028-01-31", "2028-02-01", "2028-02-29", "2028-03-01")])
    report = run_job(groww_store, "reconcile", date(2028, 3, 1), sources={"play_store": source})
    assert report.collection[0]["inserted"] == 2


@pytest.mark.parametrize("records", [[], _baseline()[:5]])
def test_COL_08_zero_reviews(groww_store, composio, records):
    assert run_job(groww_store, "daily", MONDAY, sources=_sources([])).status == "ok"
    run_job(groww_store, "backfill", MONDAY, sources=_sources(records), mcp_client=composio.client())
    report = run_job(groww_store, "pulse", MONDAY, mcp_client=composio.client())
    assert (report.status, report.succeeded) == ("low_volume", True)
    assert composio.calls == []
    assert groww_store.count_publish_states() == 0
    saved = json.loads((outputs_root() / "groww" / report.week_start / "run_report.json").read_text(encoding="utf-8"))
    assert (saved["status"], saved["min_reviews"]) == ("low_volume", load_pulse_config().note.min_reviews)


def test_COL_08_app_without_reviews_never_reads_another_apps_csv(swiggy, composio):
    swiggy.set_status("active")
    run_job(swiggy, "pulse", MONDAY, mcp_client=composio.client())
    assert swiggy.count_reviews() == 0


def test_ingest_stage_requires_an_explicit_file(groww_store):
    with pytest.raises(ValueError, match="Pass --file"):
        run_full_pipeline(groww_store, "2026-11-09", stage_limit="ingest", dry_run=True)
    assert groww_store.get_active_run_ids() == []


def test_COL_11_backfill_then_pulse(swiggy, composio):
    report = run_job(swiggy, "backfill", MONDAY, sources=_sources(_baseline()), mcp_client=composio.client())
    assert (report.status, report.week_start) == ("published", "2026-11-09")
    assert swiggy.refresh().status == "active"
    state = swiggy.get_publish_state("2026-11-09")
    assert state.doc_id and state.draft_id
    again = run_job(swiggy, "pulse", MONDAY, mcp_client=composio.client())
    assert again.status == "published"
    assert composio.tools_called().count("GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN") == 1
    assert composio.tools_called().count("GMAIL_CREATE_EMAIL_DRAFT") == 1


def test_note_dates_and_counts_match_the_analyzed_window(groww_store, composio):
    records = _baseline() + [
        {"platform": "play_store", "rating": 4, "title": None, "date": d, "app_version": None,
         "text": f"Portfolio screen shows the right balance on {d} for me"}
        for d in ("2026-08-23", "2026-08-24", "2026-11-15", "2026-11-16")
    ]
    run_job(groww_store, "backfill", MONDAY, sources=_sources(records), mcp_client=composio.client())
    run = groww_store.latest_themed_run_for_week("2026-11-09")
    assert (run.window_start, run.window_end) == ("2026-08-24", "2026-11-15")
    note_dir = outputs_root() / "groww" / "2026-11-09"
    count = len(groww_store.get_reviews_in_window("2026-08-24", "2026-11-15"))
    assert count < groww_store.count_reviews()
    for name in ("note.md", "note.html", "note.txt"):
        text = (note_dir / name).read_text(encoding="utf-8")
        assert "Reviews 2026-08-24 to 2026-11-15" in text
        assert f"Google Play {count:,}" in text


def test_note_refuses_a_run_without_a_stored_window(groww_store, composio):
    run_job(groww_store, "backfill", MONDAY, sources=_sources(_baseline()), mcp_client=composio.client())
    with groww_store.connector.session() as s:
        s.execute("UPDATE runs SET window_start = NULL, window_end = NULL")
    with pytest.raises(ValueError, match="no stored review window"):
        build_and_validate_pulse_note(groww_store, "2026-11-09")


def test_failed_backfill_publishes_nothing(swiggy, composio):
    report = run_job(swiggy, "backfill", MONDAY, sources=_sources(error=RuntimeError("x")), mcp_client=composio.client())
    assert (report.status, swiggy.refresh().status) == ("failed", "failed")
    assert composio.calls == []


@pytest.mark.parametrize("status", LIVE_NON_ACTIVE)
def test_pulse_needs_an_active_app(swiggy, status):
    swiggy.set_status(status)
    with pytest.raises(JobRefused, match="needs an active app"):
        run_job(swiggy, "pulse", MONDAY)


class ArchivingSource(FakeSource):
    def __init__(self, store, app_key, records):
        super().__init__("play_store", records)
        self._store, self._app_key = store, app_key

    def fetch(self, window_start, window_end):
        self._store.set_app_status(self._app_key, "archived")
        return super().fetch(window_start, window_end)


class ArchivingClient:
    def __init__(self, client, store, app_key, during):
        self._client, self._store, self._app_key, self._during = client, store, app_key, during

    def verify_accounts(self):
        self._archive_when("verify_accounts")
        return self._client.verify_accounts()

    def call(self, capability, arguments):
        self._archive_when(capability)
        return self._client.call(capability, arguments)

    def _archive_when(self, step):
        if step == self._during:
            self._store.set_app_status(self._app_key, "archived")


def test_APP_13_archive_during_backfill_stays_archived(pulse_store, swiggy, composio):
    source = ArchivingSource(pulse_store, "swiggy", _baseline())
    report = run_job(swiggy, "backfill", MONDAY, sources={"play_store": source}, mcp_client=composio.client())
    assert (report.status, report.succeeded) == ("stopped_archived", True)
    app = pulse_store.get_app("swiggy")
    assert app.status == "archived" and app.archived_at
    assert composio.calls == []


@pytest.mark.parametrize("during, expected_tools", [
    ("verify_accounts", []),
    ("docs.create", ["GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN"]),
])
def test_APP_13_archive_during_run(pulse_store, swiggy, composio, during, expected_tools):
    client = ArchivingClient(composio.client(), pulse_store, "swiggy", during)
    report = run_job(swiggy, "backfill", MONDAY, sources=_sources(_baseline()), mcp_client=client)
    assert (report.status, report.succeeded) == ("stopped_archived", True)
    assert composio.tools_called() == expected_tools
    state = swiggy.get_publish_state("2026-11-09")
    assert state is None or (state.draft_id is None and state.content_hash is None)


@pytest.mark.parametrize("mode", JOB_MODES)
def test_APP_13_job_on_an_archived_app_stops_cleanly(pulse_store, swiggy, composio, mode):
    pulse_store.set_app_status("swiggy", "archived")
    source = FakeSource("play_store", _baseline())
    report = run_job(swiggy, mode, MONDAY, sources={"play_store": source}, mcp_client=composio.client())
    assert (report.status, source.calls, composio.calls) == ("stopped_archived", 0, [])


def test_APP_13_publisher_refuses_an_archived_app(groww_store, composio):
    groww_store.set_status("archived")
    with pytest.raises(PublishStoppedArchived):
        PulsePublisher(groww_store, composio.client()).publish_pulse("2026-11-09", "note", TEST_RECIPIENT)
    assert composio.calls == []


def test_job_status_change_cannot_revive_an_archived_app(groww_store):
    groww_store.set_status("archived")
    for status in ("active", "failed", "backfilling"):
        assert groww_store.set_status(status).status == "archived"


def test_secrets_reach_only_the_steps_that_need_them():
    assert "GEMINI_API_KEY" not in PULSE_TEXT
    run = PULSE_WORKFLOW["jobs"]["run"]
    publishing = ("COMPOSIO_MCP_URL", "COMPOSIO_API_KEY", "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID",
                  "COMPOSIO_GMAIL_ACCOUNT_ID", "PULSE_EMAIL_TO")
    job_env = next(s for s in run["steps"] if s.get("id") == "job")["env"]
    for name in publishing:
        assert name not in run["env"]
        assert job_env[name] == (
            f"${{{{ (matrix.mode == 'pulse' || matrix.mode == 'backfill') && secrets.{name} || '' }}}}"
        )
    for workflow in (PULSE_WORKFLOW, CI_WORKFLOW):
        assert workflow["permissions"] == {"contents": "read"}


def test_no_expression_is_interpolated_into_shell():
    for workflow in (PULSE_WORKFLOW, CI_WORKFLOW):
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                assert "${{" not in step.get("run", ""), "Pass the value through env. Rule: no-inline-expression."


def test_ci_runs_every_gate():
    commands = [s.get("run", "") for job in CI_WORKFLOW["jobs"].values() for s in job["steps"]]
    for gate in ("ruff check", "mypy", "python -m pytest", "gitleaks", "actionlint", "npm test", "npm run build"):
        assert any(gate in c for c in commands), gate


def test_theme_scores_survive_the_store(groww_store):
    summary = run_full_pipeline(
        groww_store, "2026-11-09", csv_path=PROJECT_ROOT / "tests" / "fixtures" / "reviews_baseline.csv",
        stage_limit="themes", dry_run=True,
    )["themes"]
    expected = {t["theme_id"]: (t["neg_share"], t["priority_score"]) for t in summary["themes"]}
    stored = {t.theme_id: (t.neg_share, t.priority_score) for t in groww_store.get_themes(summary["run_id"])}
    assert stored == expected
    assert any(neg > 0 for neg, _ in stored.values())


def test_rerun_with_fewer_themes_drops_the_stale_ones(groww_store):
    def theme(n, neg_share=0.5):
        return {"theme_id": f"t{n}", "label": f"L{n}", "description": "d", "review_count": 1, "share_pct": 0.2,
                "avg_rating": 3.0, "is_top3": 1, "neg_share": neg_share, "priority_score": neg_share / 5, "member_review_ids": []}

    def save(themes):
        groww_store.save_theme_run("run1", "2026-11-09", "2026-08-24", "2026-11-15", 5, 5, 3.0, 12.0, themes)

    save([theme(n) for n in range(5)])
    save([theme(n, neg_share=0.75) for n in range(3)])
    stored = groww_store.get_themes("run1")
    assert sorted(t.theme_id for t in stored) == ["t0", "t1", "t2"]
    assert {(t.neg_share, t.priority_score) for t in stored} == {(0.75, 0.15)}


def test_version_3_database_gains_theme_scores(tmp_path):
    path = tmp_path / "v3.db"
    store = sqlite_store(path).for_app("groww")
    records = [{"platform": "play_store", "rating": r, "title": None, "text": f"Orders fail at market open {r}",
                "date": "2026-11-10", "app_version": None} for r in (1, 2, 5, 4)]
    run_job(store, "daily", date(2026, 11, 10), sources=_sources(records))
    ids = [r.review_id for r in store.get_reviews_in_window("2026-11-01", "2026-11-30")]
    store.save_theme_run("run1", "2026-11-09", "2026-08-24", "2026-11-15", 4, 4, 3.0, 12.0, [
        {"theme_id": "t1", "label": "L", "description": "d", "review_count": 4, "share_pct": 1.0, "avg_rating": 3.0,
         "is_top3": 1, "neg_share": 0.0, "priority_score": 0.0, "member_review_ids": ids}])
    conn = sqlite3.connect(path)
    conn.execute("ALTER TABLE themes DROP COLUMN neg_share")
    conn.execute("ALTER TABLE themes DROP COLUMN priority_score")
    conn.execute("PRAGMA user_version = 3")
    conn.commit()
    conn.close()
    theme = sqlite_store(path).for_app("groww").get_themes("run1")[0]
    assert (theme.neg_share, theme.priority_score) == (0.5, 0.8)


def test_parallel_jobs_can_open_one_postgres_store():
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    dsn = _fresh_postgres_dsn()
    errors = []

    def open_it():
        try:
            for _ in range(5):
                postgres_store(dsn).for_app("groww").set_status("active")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=open_it) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


def test_postgres_migrations_run_once():
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    store = postgres_store(_fresh_postgres_dsn())
    with store.connector.session() as s:
        s.execute("UPDATE pulse_internal.applied_migrations SET applied_at = '2000-01-01'")
    store.connector.apply_schema()
    with store.connector.session() as s:
        rows = s.fetchall("SELECT name FROM pulse_internal.applied_migrations WHERE applied_at > '2000-01-02'")
        total = s.scalar("SELECT COUNT(*) AS n FROM pulse_internal.applied_migrations")
    assert rows == []
    assert total == len(list((PROJECT_ROOT / "supabase" / "migrations").glob("*.sql")))


def test_existing_postgres_database_gains_theme_scores():
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    import psycopg

    dsn = _fresh_postgres_dsn()
    with psycopg.connect(dsn) as conn:
        for name in ("20261123000000_multi_app.sql", "20261124000000_collectors.sql"):
            conn.execute((PROJECT_ROOT / "supabase" / "migrations" / name).read_text(encoding="utf-8"))
        conn.execute("INSERT INTO runs (app_key, run_id, week_start, status, created_at) "
                     "VALUES ('groww', 'run1', '2026-11-09', 'published', '2026-11-16')")
        conn.execute("INSERT INTO themes (app_key, theme_id, run_id, label, description, review_count, share_pct, avg_rating) "
                     "VALUES ('groww', 't1', 'run1', 'L', 'd', 4, 1.0, 3.0)")
        for n, rating in enumerate((1, 2, 5, 4)):
            conn.execute("INSERT INTO reviews (app_key, review_id, platform, rating, text, date, raw_hash, created_at) "
                         "VALUES ('groww', %s, 'play_store', %s, 'text', '2026-11-10', 'h', '2026-11-16')", (f"r{n}", rating))
            conn.execute("INSERT INTO review_themes (app_key, review_id, theme_id) VALUES ('groww', %s, 't1')", (f"r{n}",))
    theme = postgres_store(dsn).for_app("groww").get_themes("run1")[0]
    assert (theme.neg_share, theme.priority_score) == (0.5, 0.8)

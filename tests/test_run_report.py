import json
from datetime import date

import pytest

from src.config import PROJECT_ROOT, outputs_root
from src.note.engine import build_and_validate_pulse_note
from src.run_report import RUN_REPORT_NAME, scrub_report, write_run_report
from src.scheduler.jobs import run_job
from tests.test_phase11_scheduler import MONDAY, _baseline, _sources

PULSE_WEEK = "2026-11-09"
FUTURE_RUN_ID = "run_2026-11-30_1796461877636"


def _report(store):
    return json.loads((outputs_root() / store.app_key / PULSE_WEEK / RUN_REPORT_NAME).read_text(encoding="utf-8"))


def test_published_report_is_valid_json_with_its_links(groww_store, composio):
    run_job(groww_store, "backfill", MONDAY, sources=_sources(_baseline()), mcp_client=composio.client())
    state = groww_store.get_publish_state(PULSE_WEEK)
    published = _report(groww_store)["publish"]
    assert published["doc_url"].startswith("https://docs.google.com/document/d/")
    assert (published["doc_url"], published["doc_id"], published["draft_id"]) == (
        state.doc_url, state.doc_id, state.draft_id)


@pytest.mark.parametrize("leak", [
    "mail someone@example.com", "call 9876543210", "see https://example.com/a?b=c now", 'quote " and 9876543210\n',
])
def test_free_text_is_scrubbed_and_stays_valid_json(tmp_path, leak):
    path = write_run_report(tmp_path, {"publish": {"error": leak}, "errors": [leak], "word_count": 9876543210})
    saved = json.loads(path.read_text(encoding="utf-8"))
    for text in (saved["publish"]["error"], saved["errors"][0]):
        assert "[REDACTED]" in text
        assert not {"someone@example.com", "9876543210", "https://example.com/a?b=c"} & set(text.split())
    assert saved["word_count"] == 9876543210


def test_run_id_that_looks_like_a_phone_number_is_kept():
    assert scrub_report({"run_id": FUTURE_RUN_ID, "note": FUTURE_RUN_ID}) == {
        "run_id": FUTURE_RUN_ID, "note": scrub_report(FUTURE_RUN_ID)}
    assert scrub_report(FUTURE_RUN_ID) != FUTURE_RUN_ID


def test_clean_text_is_untouched():
    assert scrub_report({"label": " Charges \u2605 & Pricing "}) == {"label": " Charges \u2605 & Pricing "}


def test_only_one_module_writes_run_reports():
    offenders = [
        p.relative_to(PROJECT_ROOT).as_posix()
        for p in (PROJECT_ROOT / "src").rglob("*.py")
        if p.name != "run_report.py" and f'"{RUN_REPORT_NAME}"' in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], "Writing run_report.json here is banned. Use write_run_report."


@pytest.mark.parametrize("first_day, weeks, short", [("2026-10-12", 4.1, True), ("2026-09-07", 9.1, False)])
def test_note_flags_the_real_coverage(groww_store, composio, first_day, weeks, short):
    records = [r for r in _baseline() if r["date"] >= first_day]
    assert min(r["date"] for r in records) == first_day
    report = run_job(groww_store, "backfill", MONDAY, sources=_sources(records), mcp_client=composio.client())
    assert report.status == "published"
    assert groww_store.latest_themed_run_for_week(PULSE_WEEK).coverage_weeks == weeks
    saved = _report(groww_store)
    assert (saved["coverage_weeks"], saved["short_coverage_flag"]) == (weeks, short)
    note, rendered, validation, _ = build_and_validate_pulse_note(groww_store, PULSE_WEEK)
    assert validation.is_valid and validation.word_count <= 250
    assert (f"Available reviews span {weeks:.1f} weeks" in rendered) is short
    assert (note.coverage_weeks, note.short_coverage_flag) == (weeks, short)


def test_full_twelve_weeks_is_not_flagged(groww_store, composio):
    edge = [{"platform": "play_store", "rating": 4, "title": None, "date": d, "app_version": None,
             "text": f"Portfolio screen shows the right balance on {d} for me"} for d in ("2026-08-24", "2026-11-15")]
    run_job(groww_store, "backfill", date(2026, 11, 16), sources=_sources(_baseline() + edge),
            mcp_client=composio.client())
    assert groww_store.latest_themed_run_for_week(PULSE_WEEK).coverage_weeks == 12.0

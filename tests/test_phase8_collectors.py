import copy
import csv
import json
from datetime import date, datetime
from pathlib import Path

import pytest
from google_play_scraper.exceptions import ExtraHTTPError

from src.config import load_pulse_config
from src.ingest.app_store import AppStoreSource, map_app_store_entry, parse_feed_page, parse_feed_xml
from src.ingest.collect import CollectionRefused, collect_app, collection_window
from src.ingest.play_store import PAGE_DELAY_S, PlayStoreSource, map_play_item
from src.ingest.sources import ListingNotFound, SourceResult
from src.note.coverage import build_store_coverage, sources_line, store_scope_errors
from src.note.models import StoreCoverage, WeeklyPulseNote
from src.pipeline import build_parser
from src.store.errors import AppIdentityFrozen
from src.store.models import AppRecord

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "stores"
PLAY_PAGE = json.loads((FIXTURES / "play_store_page.json").read_text(encoding="utf-8"))
APP_JSON = (FIXTURES / "app_store_page.synthetic.json").read_bytes()
APP_XML = (FIXTURES / "app_store_page.synthetic.xml").read_bytes()
EMPTY_JSON = json.dumps({"feed": {"author": {"name": {"label": "iTunes Store"}}}}).encode()
EMPTY_XML = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><id>x</id></feed>'
ALLOWLIST = {"platform", "rating", "title", "text", "date", "app_version"}
IDENTITY_VALUES = (
    "Fixture Reviewer", "fixture-review-id", "example.invalid", "Fixture developer reply",
)
TODAY = date(2026, 11, 23)


def _play_items():
    items = copy.deepcopy(PLAY_PAGE)
    for item in items:
        item["at"] = datetime.fromisoformat(item["at"])
    return items


def _no_sleep(_seconds):
    return None


class FakeSource:
    def __init__(self, platform, records=None, error=None):
        self.platform = platform
        self.records = records or []
        self.error = error
        self.calls = 0

    def fetch(self, window_start, window_end):
        self.calls += 1
        if self.error:
            raise self.error
        records = [r for r in self.records if window_start <= r["date"] <= window_end]
        return SourceResult(records=records, fetched=len(records), pages=1, covered_start=window_start)


def _raw(platform, day, text, rating=4):
    return {"platform": platform, "rating": rating, "title": None, "text": text, "date": day, "app_version": "1.0"}


@pytest.fixture
def config():
    return load_pulse_config("config/pulse.yaml")


def _assert_identity_free(blob: str):
    for value in IDENTITY_VALUES:
        assert value not in blob


def test_COL_01_play_identity_never_extracted(groww_store, tmp_path, config):
    mapped = [map_play_item(i) for i in _play_items()]
    assert mapped
    for m in mapped:
        if m is not None:
            assert set(m) == ALLOWLIST
    _assert_identity_free(json.dumps(mapped))
    pages = iter([(_play_items(), None)])
    source = PlayStoreSource("com.x", "in", "en", fetch_page=lambda token: next(pages),
                             check_listing=lambda: None, sleep=_no_sleep)
    collect_app(groww_store, "backfill", TODAY, config, sources={"play_store": source}, raw_dir=tmp_path)
    with groww_store.connector.session() as s:
        rows = s.fetchall("SELECT * FROM reviews WHERE app_key = 'groww'")
    assert rows
    _assert_identity_free(json.dumps(rows))
    _assert_identity_free("".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.csv")))


def test_COL_01_app_store_identity_never_extracted():
    entries = parse_feed_page(APP_JSON) + parse_feed_xml(APP_XML)
    mapped = [map_app_store_entry(e) for e in entries]
    assert len(mapped) == 4
    for m in mapped:
        assert set(m) == ALLOWLIST
    _assert_identity_free(json.dumps(mapped))


def test_COL_02_disabled_store_no_calls(groww_store, tmp_path, config):
    config.sources.app_store.enabled = False
    play = FakeSource("play_store", [_raw("play_store", "2026-11-22", "Charts load slowly at market open")])
    apple = FakeSource("app_store", [_raw("app_store", "2026-11-22", "Login fails after update")])
    report = collect_app(groww_store, "daily", TODAY, config,
                         sources={"play_store": play, "app_store": apple}, raw_dir=tmp_path)
    assert apple.calls == 0
    statuses = {r.platform: r.status for r in report.runs}
    assert statuses == {"play_store": "ok", "app_store": "skipped_disabled"}


def _feed_with_dates(dates):
    entries = []
    base = json.loads(APP_JSON)["feed"]["entry"][0]
    for i, day in enumerate(dates):
        entry = copy.deepcopy(base)
        entry["updated"] = {"label": f"{day}T10:00:00-07:00"}
        entry["content"] = {"label": f"Review number {i} about slow order placement during trading hours"}
        entries.append(entry)
    return json.dumps({"feed": {"entry": entries}}).encode()


class FakeHttp:
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        handler = self.responses
        return handler(url, len(self.urls)) if callable(handler) else handler.pop(0)


def test_COL_03_app_store_cap_flagged():
    page_body = _feed_with_dates(["2026-11-20"] * 50)
    http = FakeHttp(lambda url, n: (200, page_body))
    result = AppStoreSource("1", "in", http_get=http, sleep=_no_sleep).fetch("2026-09-01", "2026-11-23")
    assert result.pages == 10
    assert result.source_limit_hit is True
    assert result.covered_start == "2026-11-20"


def test_COL_13_feed_gaps_flagged_and_xml_fallback():
    def respond(url, n):
        if "page=1/" in url:
            return 200, EMPTY_JSON if url.endswith("json") else EMPTY_XML
        if "page=2/" in url:
            return 200, EMPTY_JSON if url.endswith("json") else APP_XML
        return 200, _feed_with_dates(["2026-11-10", "2026-08-01"])

    result = AppStoreSource("1", "in", http_get=FakeHttp(respond), sleep=_no_sleep).fetch("2026-09-01", "2026-11-23")
    assert result.feed_gaps == 1
    assert result.source_limit_hit is True
    assert {r["date"] for r in result.records} == {"2026-11-19", "2026-11-10"}


def test_app_store_stops_at_window_start():
    http = FakeHttp([(200, APP_JSON)])
    result = AppStoreSource("1", "in", http_get=http, sleep=_no_sleep).fetch("2026-09-01", "2026-11-23")
    assert result.pages == 1
    assert result.source_limit_hit is False
    assert [r["date"] for r in result.records] == ["2026-11-20", "2026-11-19"]


def test_COL_04_daily_overlap_dedup(groww_store, tmp_path, config):
    play = FakeSource("play_store", [
        _raw("play_store", "2026-11-21", "Order placement freezes during the morning session"),
        _raw("play_store", "2026-11-22", "Portfolio page shows wrong returns after the update"),
    ])
    first = collect_app(groww_store, "daily", TODAY, config, sources={"play_store": play}, raw_dir=tmp_path)
    second = collect_app(groww_store, "daily", date(2026, 11, 24), config, sources={"play_store": play}, raw_dir=tmp_path)
    assert first.runs[0].inserted == 2
    assert second.runs[0].inserted == 0
    assert groww_store.count_reviews() == 2


def test_COL_05_reconcile_fills_gaps(groww_store, tmp_path, config):
    october = [_raw("play_store", f"2026-10-{d:02d}", f"Review on day {d} about delayed fund settlement") for d in (5, 15, 25)]
    collect_app(groww_store, "daily", date(2026, 10, 6), config,
                sources={"play_store": FakeSource("play_store", october)}, raw_dir=tmp_path)
    report = collect_app(groww_store, "reconcile", date(2026, 11, 1), config,
                         sources={"play_store": FakeSource("play_store", october)}, raw_dir=tmp_path)
    assert (report.window_start, report.window_end) == ("2026-10-01", "2026-10-31")
    assert report.runs[0].inserted == 2
    assert groww_store.count_reviews() == 3


def test_COL_06_play_failure_isolated(pulse_store, tmp_path, config):
    pulse_store.insert_app(AppRecord("swiggy", "Swiggy", "active", play_package_id="in.swiggy.android"))
    groww = pulse_store.for_app("groww")
    swiggy = pulse_store.for_app("swiggy")
    broken = FakeSource("play_store", error=ValueError("unexpected shape"))
    apple = FakeSource("app_store", [_raw("app_store", "2026-11-22", "Login fails after the latest update")])
    report = collect_app(groww, "daily", TODAY, config, sources={"play_store": broken, "app_store": apple}, raw_dir=tmp_path)
    assert {r.platform: r.status for r in report.runs} == {"play_store": "failed", "app_store": "ok"}
    assert "unexpected shape" in report.runs[0].error
    assert report.app_status == "active"
    other = collect_app(swiggy, "daily", TODAY, config, raw_dir=tmp_path, sources={
        "play_store": FakeSource("play_store", [_raw("play_store", "2026-11-22", "Delivery arrived cold and late")])})
    assert other.runs[0].status == "ok"


def test_play_unexpected_shape_raises():
    pages = iter([([{"content": "no score"}], None)])
    source = PlayStoreSource("com.x", "in", "en", fetch_page=lambda t: next(pages), check_listing=lambda: None, sleep=_no_sleep)
    with pytest.raises(Exception, match="without score or date"):
        source.fetch("2026-09-01", "2026-11-23")


def test_COL_07_rate_limit_backoff():
    sleeps = []
    http = FakeHttp([(429, b""), (503, b""), (200, APP_JSON)])
    result = AppStoreSource("1", "in", http_get=http, sleep=sleeps.append).fetch("2026-09-01", "2026-11-23")
    assert len(result.records) == 2
    assert sleeps == [2.0, 4.0]


def test_COL_07_rate_limit_gives_up_after_three(groww_store, tmp_path, config):
    source = AppStoreSource("1", "in", http_get=FakeHttp([(429, b"")] * 3), sleep=_no_sleep)
    report = collect_app(groww_store, "daily", TODAY, config, sources={"app_store": source}, raw_dir=tmp_path)
    assert report.runs[0].status == "failed"
    assert "SourceUnavailable" in report.runs[0].error


def test_play_retries_extra_http_error():
    calls = []

    def fetch(token):
        calls.append(token)
        if len(calls) < 3:
            raise ExtraHTTPError("429")
        return _play_items(), None

    sleeps = []
    result = PlayStoreSource("com.x", "in", "en", fetch_page=fetch, check_listing=lambda: None,
                             sleep=sleeps.append).fetch("2026-01-01", "2026-12-31")
    assert len(calls) == 3
    assert sleeps == [2.0, 4.0]
    assert result.records


def test_play_pages_with_delay_and_stops_at_window_start():
    items = _play_items()
    newest = items[: len(items) // 2]
    older = items[len(items) // 2:]
    for item in older:
        item["at"] = datetime(2026, 1, 1)
    pages = iter([(newest, "token-1"), (older, "token-2"), ([], None)])
    tokens = []
    sleeps = []

    def fetch(token):
        tokens.append(token)
        return next(pages)

    result = PlayStoreSource("com.x", "in", "en", fetch_page=fetch, check_listing=lambda: None,
                             sleep=sleeps.append).fetch("2026-09-01", "2026-11-23")
    assert tokens == [None, "token-1"]
    assert sleeps == [PAGE_DELAY_S]
    assert result.source_limit_hit is False
    assert all(r["date"] >= "2026-09-01" for r in result.records)


def test_COL_08_zero_reviews(groww_store, tmp_path, config):
    report = collect_app(groww_store, "daily", TODAY, config,
                         sources={"play_store": FakeSource("play_store", [])}, raw_dir=tmp_path)
    assert report.runs[0].status == "ok"
    assert report.runs[0].inserted == 0


def test_COL_09_delisted_play_app(groww_store, tmp_path, config):
    def gone():
        raise ListingNotFound("Play Store listing not found: com.x")

    source = PlayStoreSource("com.x", "in", "en", fetch_page=lambda t: ([], None), check_listing=gone, sleep=_no_sleep)
    report = collect_app(groww_store, "daily", TODAY, config, sources={"play_store": source}, raw_dir=tmp_path)
    assert report.runs[0].status == "failed"
    assert "listing not found" in report.runs[0].error
    assert groww_store.app.status == "failed"


def test_COL_09_delisted_app_store_app():
    source = AppStoreSource("1", "in", http_get=FakeHttp([(404, b"")]), sleep=_no_sleep)
    with pytest.raises(ListingNotFound):
        source.fetch("2026-09-01", "2026-11-23")


def test_COL_10_cross_store_not_merged(groww_store, tmp_path, config):
    text = "Withdrawals take three days to reach my bank account"
    collect_app(groww_store, "daily", TODAY, config, raw_dir=tmp_path, sources={
        "play_store": FakeSource("play_store", [_raw("play_store", "2026-11-22", text)]),
        "app_store": FakeSource("app_store", [_raw("app_store", "2026-11-22", text)]),
    })
    reviews = groww_store.get_reviews_in_window("2026-11-01", "2026-11-30")
    assert sorted(r.platform for r in reviews) == ["app_store", "play_store"]


def test_COL_11_backfill_sets_active(pulse_store, tmp_path, config):
    pulse_store.insert_app(AppRecord("swiggy", "Swiggy", "pending_backfill", play_package_id="in.swiggy.android"))
    swiggy = pulse_store.for_app("swiggy")
    report = collect_app(swiggy, "backfill", TODAY, config, raw_dir=tmp_path, sources={
        "play_store": FakeSource("play_store", [_raw("play_store", "2026-10-01", "Delivery partner never arrived")])})
    assert report.app_status == "active"
    assert (report.window_start, report.window_end) == ("2026-08-31", "2026-11-23")


def test_backfill_failure_marks_app_failed(pulse_store, tmp_path, config):
    pulse_store.insert_app(AppRecord("swiggy", "Swiggy", "pending_backfill", play_package_id="in.swiggy.android"))
    swiggy = pulse_store.for_app("swiggy")
    report = collect_app(swiggy, "backfill", TODAY, config, raw_dir=tmp_path,
                         sources={"play_store": FakeSource("play_store", error=RuntimeError("boom"))})
    assert report.app_status == "failed"


def test_archived_app_not_collected(groww_store, tmp_path, config):
    groww_store.set_status("archived")
    with pytest.raises(CollectionRefused):
        collect_app(groww_store, "daily", TODAY, config, sources={}, raw_dir=tmp_path)


def test_COL_12_lang_from_feed(groww_store, tmp_path, config):
    hindi = "यह ऐप बहुत अच्छा है लेकिन पैसे निकालने में देरी होती है"
    collect_app(groww_store, "daily", TODAY, config, raw_dir=tmp_path, sources={
        "app_store": FakeSource("app_store", [_raw("app_store", "2026-11-22", hindi)])})
    review = groww_store.get_reviews_in_window("2026-11-01", "2026-11-30")[0]
    assert review.lang == "hi"
    assert review.quote_eligible == 0


def test_collection_windows():
    assert collection_window("daily", TODAY, 12) == ("2026-11-21", "2026-11-23")
    assert collection_window("backfill", TODAY, 12) == ("2026-08-31", "2026-11-23")
    assert collection_window("reconcile", date(2026, 1, 1), 12) == ("2025-12-01", "2025-12-31")
    with pytest.raises(ValueError):
        collection_window("weekly", TODAY, 12)


def test_raw_archive_keeps_only_allowlisted_columns(groww_store, tmp_path, config):
    collect_app(groww_store, "daily", TODAY, config, raw_dir=tmp_path, sources={
        "play_store": FakeSource("play_store", [_raw("play_store", "2026-11-22", "App crashes on the orders page")])})
    archive = next(tmp_path.glob("play_store_daily_*.csv"))
    header = next(csv.reader(archive.open(encoding="utf-8")))
    assert set(header) == ALLOWLIST


def test_store_coverage_in_note_header(groww_store, tmp_path, config):
    collect_app(groww_store, "daily", TODAY, config, raw_dir=tmp_path, sources={
        "play_store": FakeSource("play_store", [_raw("play_store", "2026-11-22", "Charts load slowly at market open")]),
        "app_store": FakeSource("app_store", error=RuntimeError("feed down")),
    })
    coverage = build_store_coverage(groww_store, "2026-11-01", "2026-11-30")
    assert [(c.platform, c.reviews, c.caveat) for c in coverage] == [
        ("play_store", 1, None), ("app_store", 0, "last collection failed")]
    note = WeeklyPulseNote("2026-11-23", "2026-11-01", "2026-11-30", "Groww", store_coverage=coverage)
    assert sources_line(note) == "Google Play 1 · App Store 0 (last collection failed)"


def test_store_coverage_flags_feed_gaps(groww_store):
    collection_id = groww_store.start_collection("app_store", "daily", "2026-11-21", "2026-11-23")
    groww_store.finish_collection(collection_id, "ok", source_limit_hit=True, feed_gaps=2, covered_start="2026-11-21")
    coverage = {c.platform: c for c in build_store_coverage(groww_store, "2026-11-01", "2026-11-30")}
    assert coverage["app_store"].caveat == "partial, store feed had gaps"


def test_NOT_14_note_names_exactly_its_stores():
    play_only = WeeklyPulseNote("w", "s", "e", "Groww", store_coverage=[StoreCoverage("play_store", 10)])
    both = WeeklyPulseNote("w", "s", "e", "Groww", store_coverage=[
        StoreCoverage("play_store", 10), StoreCoverage("app_store", 4)])
    assert store_scope_errors(play_only, "Google Play 10") == []
    assert store_scope_errors(play_only, "Google Play 10 · App Store 4")
    assert store_scope_errors(play_only, "Google Play 10, iOS users")
    assert store_scope_errors(both, "Google Play 10")
    assert store_scope_errors(both, "Google Play 10 · App Store 4") == []


def test_attach_listing_once(pulse_store):
    pulse_store.insert_app(AppRecord("swiggy", "Swiggy", "active", play_package_id="in.swiggy.android"))
    assert pulse_store.attach_listing("swiggy", "app_store", "989540920").app_store_id == "989540920"
    assert pulse_store.attach_listing("swiggy", "app_store", "989540920").app_store_id == "989540920"
    with pytest.raises(AppIdentityFrozen):
        pulse_store.attach_listing("swiggy", "app_store", "111")


def test_collect_cli_parses():
    args = build_parser().parse_args(["collect", "--app", "groww", "--mode", "backfill", "--today", "2026-11-23"])
    assert (args.app, args.mode, args.today) == ("groww", "backfill", "2026-11-23")
    with pytest.raises(SystemExit):
        build_parser().parse_args(["collect", "--app", "groww", "--mode", "weekly"])

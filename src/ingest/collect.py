from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from src.config import PulseConfig, load_pulse_config, raw_reviews_dir
from src.ingest.app_store import AppStoreSource
from src.ingest.persist import clean_raw_reviews
from src.ingest.play_store import PlayStoreSource
from src.ingest.sources import ListingNotFound, ReviewSource
from src.store.models import PLATFORMS, CollectionRunRecord
from src.store.store import AppStore

COLLECTION_MODES = ("backfill", "daily", "reconcile")
DAILY_LOOKBACK_DAYS = 2
COLLECTABLE_STATUSES = ("pending_backfill", "backfilling", "active", "failed")
ERROR_MAX_CHARS = 300


class CollectionRefused(Exception):
    pass


@dataclass
class CollectionReport:
    app_key: str
    mode: str
    window_start: str
    window_end: str
    runs: List[CollectionRunRecord]
    app_status: str

    @property
    def failed(self) -> bool:
        return any(r.status == "failed" for r in self.runs)

    def to_dict(self) -> dict:
        return {
            "app_key": self.app_key,
            "mode": self.mode,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "app_status": self.app_status,
            "runs": [
                {
                    "platform": r.platform,
                    "status": r.status,
                    "fetched": r.fetched,
                    "inserted": r.inserted,
                    "covered_start": r.covered_start,
                    "source_limit_hit": bool(r.source_limit_hit),
                    "feed_gaps": r.feed_gaps,
                    "error": r.error,
                }
                for r in self.runs
            ],
        }


def collection_window(mode: str, today: date, weeks: int) -> Tuple[str, str]:
    if mode == "backfill":
        return (today - timedelta(weeks=weeks)).isoformat(), today.isoformat()
    if mode == "daily":
        return (today - timedelta(days=DAILY_LOOKBACK_DAYS)).isoformat(), today.isoformat()
    if mode == "reconcile":
        last_of_previous = today.replace(day=1) - timedelta(days=1)
        return last_of_previous.replace(day=1).isoformat(), last_of_previous.isoformat()
    raise ValueError(f"Unknown collection mode {mode!r}. Use one of {COLLECTION_MODES}.")


def default_sources(store: AppStore) -> Dict[str, ReviewSource]:
    app = store.app
    sources: Dict[str, ReviewSource] = {}
    if app.play_package_id:
        sources["play_store"] = PlayStoreSource(app.play_package_id, country=app.country, lang=app.lang)
    if app.app_store_id:
        sources["app_store"] = AppStoreSource(app.app_store_id, country=app.country)
    return sources


def _enabled(config: PulseConfig, platform: str) -> bool:
    return getattr(config.sources, platform).enabled


def _collect_one(
    store: AppStore, source: ReviewSource, mode: str, window: Tuple[str, str], raw_dir: Path
) -> Tuple[CollectionRunRecord, bool]:
    window_start, window_end = window
    collection_id = store.start_collection(source.platform, mode, window_start, window_end)
    try:
        result = source.fetch(window_start, window_end)
        batch = clean_raw_reviews(result.records, raw_dir / f"{source.platform}_{mode}_{window_start}_{window_end}.csv")
        inserted = store.upsert_reviews(batch.records)
    except ListingNotFound as exc:
        return store.finish_collection(collection_id, "failed", error=str(exc)[:ERROR_MAX_CHARS]), True
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"[:ERROR_MAX_CHARS]
        return store.finish_collection(collection_id, "failed", error=message), False
    run = store.finish_collection(
        collection_id,
        "ok",
        fetched=result.fetched,
        inserted=inserted,
        covered_start=result.covered_start,
        source_limit_hit=result.source_limit_hit,
        feed_gaps=result.feed_gaps,
    )
    return run, False


def collect_app(
    store: AppStore,
    mode: str,
    today: date,
    config: Optional[PulseConfig] = None,
    sources: Optional[Mapping[str, ReviewSource]] = None,
    raw_dir: Optional[Path] = None,
) -> CollectionReport:
    if mode not in COLLECTION_MODES:
        raise ValueError(f"Unknown collection mode {mode!r}. Use one of {COLLECTION_MODES}.")
    if store.app.status not in COLLECTABLE_STATUSES:
        raise CollectionRefused(f"App {store.app_key!r} is {store.app.status}; collection is not allowed.")
    config = config or load_pulse_config()
    window = collection_window(mode, today, config.window.weeks)
    sources = default_sources(store) if sources is None else sources
    raw_dir = raw_dir or raw_reviews_dir(store.app_key)
    if mode == "backfill":
        store.set_status("backfilling")

    runs: List[CollectionRunRecord] = []
    delisted = False
    for platform in PLATFORMS:
        source = sources.get(platform)
        if source is None:
            continue
        if not _enabled(config, platform):
            runs.append(store.record_skipped_collection(platform, mode, *window))
            continue
        run, not_found = _collect_one(store, source, mode, window, raw_dir)
        runs.append(run)
        delisted = delisted or not_found

    failed = any(r.status == "failed" for r in runs)
    if delisted or (mode == "backfill" and failed):
        store.set_status("failed")
    elif mode == "backfill":
        store.set_status("active")
    return CollectionReport(store.app_key, mode, window[0], window[1], runs, store.app.status)

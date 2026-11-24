from datetime import date, timedelta
from typing import List, Optional

from src.note.models import STORE_LABELS, StoreCoverage, WeeklyPulseNote
from src.store.models import PLATFORMS, CollectionRunRecord
from src.store.store import AppStore

LISTING_ATTRIBUTES = {"play_store": "play_package_id", "app_store": "app_store_id"}
IOS_WORDS = ("iOS", "iPhone")
ISO_DAY_CHARS = len("2026-01-01")


def _days(first: str, last: str) -> List[str]:
    start = date.fromisoformat(first)
    return [(start + timedelta(days=n)).isoformat() for n in range((date.fromisoformat(last) - start).days + 1)]


def _reaches(run: CollectionRunRecord, day: str) -> bool:
    if run.covered_start is None or run.feed_gaps:
        return False
    starts_in_time = run.covered_start < day if run.source_limit_hit else run.covered_start <= day
    return starts_in_time and day <= run.window_end


def _collected_despite_gap(day: str, gap: CollectionRunRecord, runs: List[CollectionRunRecord]) -> bool:
    return any(
        _reaches(r, day) and (r.collection_id > gap.collection_id or r.started_at[:ISO_DAY_CHARS] > day) for r in runs
    )


def _missing_days(
    gap: CollectionRunRecord, runs: List[CollectionRunRecord], window_start: str, window_end: str
) -> List[str]:
    days = _days(max(gap.window_start, window_start), min(gap.window_end, window_end))
    return [d for d in days if not _collected_despite_gap(d, gap, runs)]


def coverage_caveat(
    collections: List[CollectionRunRecord], window_start: str, window_end: str, reviews: int
) -> Optional[str]:
    if not collections:
        return None if reviews else "not collected yet"
    if collections[-1].status == "skipped_disabled":
        return "collection disabled"
    if collections[-1].status == "failed":
        return "last collection failed"
    runs = [c for c in collections if c.status == "ok"]
    if any(c.feed_gaps and _missing_days(c, runs, window_start, window_end) for c in runs):
        return "partial, store feed had gaps"
    starts = [c.covered_start for c in runs if c.covered_start]
    if starts and min(starts) > window_start:
        return f"partial, from {min(starts)}"
    return None


def build_store_coverage(store: AppStore, window_start: str, window_end: str) -> List[StoreCoverage]:
    counts = store.platform_counts(window_start, window_end)
    coverage: List[StoreCoverage] = []
    for platform in PLATFORMS:
        listed = getattr(store.app, LISTING_ATTRIBUTES[platform]) is not None
        reviews = counts.get(platform, 0)
        if not listed and reviews == 0:
            continue
        caveat = coverage_caveat(store.finished_collections(platform), window_start, window_end, reviews)
        coverage.append(StoreCoverage(platform, reviews, caveat))
    return coverage


def sources_line(note: WeeklyPulseNote) -> str:
    parts = []
    for c in note.store_coverage:
        caveat = f" ({c.caveat})" if c.caveat else ""
        parts.append(f"{c.label} {c.reviews:,}{caveat}")
    return " · ".join(parts)


def store_scope_errors(note: WeeklyPulseNote, rendered_text: str) -> List[str]:
    covered = {c.platform for c in note.store_coverage}
    errors = []
    for platform, label in STORE_LABELS.items():
        mentioned = label in rendered_text
        if platform in covered and not mentioned:
            errors.append(f"NOT-14: Note must name its source '{label}'.")
        if platform not in covered and mentioned:
            errors.append(f"NOT-14: Note mentions '{label}' but has no {label} coverage.")
    if "app_store" not in covered and any(w in rendered_text for w in IOS_WORDS):
        errors.append("NOT-14: Note mentions iOS but has no App Store coverage.")
    return errors

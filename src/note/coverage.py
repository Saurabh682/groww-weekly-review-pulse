from typing import List, Optional

from src.note.models import STORE_LABELS, StoreCoverage, WeeklyPulseNote
from src.store.models import PLATFORMS, CollectionRunRecord
from src.store.store import AppStore

LISTING_ATTRIBUTES = {"play_store": "play_package_id", "app_store": "app_store_id"}
IOS_WORDS = ("iOS", "iPhone")


def coverage_caveat(latest: Optional[CollectionRunRecord], reviews: int) -> Optional[str]:
    if latest is None:
        return None if reviews else "not collected yet"
    if latest.status == "skipped_disabled":
        return "collection disabled"
    if latest.status == "failed":
        return "last collection failed"
    if latest.feed_gaps:
        return "partial, store feed had gaps"
    if latest.source_limit_hit and latest.covered_start:
        return f"partial, from {latest.covered_start}"
    return None


def build_store_coverage(store: AppStore, window_start: str, window_end: str) -> List[StoreCoverage]:
    counts = store.platform_counts(window_start, window_end)
    coverage: List[StoreCoverage] = []
    for platform in PLATFORMS:
        listed = getattr(store.app, LISTING_ATTRIBUTES[platform]) is not None
        reviews = counts.get(platform, 0)
        if not listed and reviews == 0:
            continue
        latest = store.latest_finished_collection(platform)
        coverage.append(StoreCoverage(platform, reviews, coverage_caveat(latest, reviews)))
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

"""Data models for persistence in SQLite and in-memory pipeline stages."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ReviewRecord:
    review_id: str
    platform: str
    rating: int
    text: str
    date: str  # YYYY-MM-DD
    title: Optional[str] = None
    app_version: Optional[str] = None
    lang: str = "en"
    low_info: int = 0
    pii_found: int = 0
    quote_eligible: int = 1
    raw_hash: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class RunRecord:
    run_id: str
    week_start: str  # YYYY-MM-DD
    status: str
    total_reviews: int = 0
    analyzed_reviews: int = 0
    avg_rating: float = 0.0
    coverage_weeks: float = 0.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    error: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass(frozen=True)
class PulseAttempt:
    week_start: str
    status: str
    window_start: str
    window_end: str
    usable_reviews: int


PLATFORMS = ("play_store", "app_store")
COLLECTION_MODES = ("backfill", "daily", "reconcile", "csv_import")
COLLECTION_STATUSES = ("running", "ok", "failed", "skipped_disabled")


@dataclass
class CollectionRunRecord:
    collection_id: int
    platform: str
    mode: str
    window_start: str
    window_end: str
    status: str
    started_at: str
    covered_start: Optional[str] = None
    fetched: int = 0
    inserted: int = 0
    source_limit_hit: int = 0
    feed_gaps: int = 0
    error: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class PublishStateRecord:
    week_start: str
    doc_id: Optional[str] = None
    doc_url: Optional[str] = None
    draft_id: Optional[str] = None
    content_hash: Optional[str] = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ThemeRecord:
    theme_id: str
    run_id: str
    label: str
    description: str
    review_count: int
    share_pct: float
    avg_rating: float
    is_top3: int = 0
    neg_share: float = 0.0
    priority_score: float = 0.0


APP_STATUSES = ("pending_backfill", "backfilling", "active", "archived", "failed")
LIVE_APP_STATUSES = ("pending_backfill", "backfilling", "active", "failed")


@dataclass
class AppRecord:
    app_key: str
    display_name: str
    status: str
    play_package_id: Optional[str] = None
    app_store_id: Optional[str] = None
    country: str = "in"
    lang: str = "en"
    category: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    archived_at: Optional[str] = None

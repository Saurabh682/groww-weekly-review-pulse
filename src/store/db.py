"""SQLite database management for Groww Weekly Review Pulse.

Enforces zero identity columns (SEC-01) and idempotent insertions.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable, List, Optional
from src.config import resolve_project_path
from src.store.models import ReviewRecord, RunRecord, PublishStateRecord


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT,
    text TEXT NOT NULL,
    date TEXT NOT NULL,
    app_version TEXT,
    lang TEXT NOT NULL DEFAULT 'en',
    low_info INTEGER NOT NULL DEFAULT 0,
    pii_found INTEGER NOT NULL DEFAULT 0,
    quote_eligible INTEGER NOT NULL DEFAULT 1,
    raw_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date);
CREATE INDEX IF NOT EXISTS idx_reviews_platform_date ON reviews(platform, date);
CREATE INDEX IF NOT EXISTS idx_reviews_low_info ON reviews(low_info);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    week_start TEXT NOT NULL,
    status TEXT NOT NULL,
    total_reviews INTEGER NOT NULL,
    analyzed_reviews INTEGER NOT NULL,
    avg_rating REAL NOT NULL,
    coverage_weeks REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS themes (
    theme_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    review_count INTEGER NOT NULL,
    share_pct REAL NOT NULL,
    avg_rating REAL NOT NULL,
    is_top3 INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS review_themes (
    review_id TEXT NOT NULL,
    theme_id TEXT NOT NULL,
    distance REAL,
    PRIMARY KEY (review_id, theme_id),
    FOREIGN KEY(review_id) REFERENCES reviews(review_id),
    FOREIGN KEY(theme_id) REFERENCES themes(theme_id)
);

CREATE TABLE IF NOT EXISTS publish_state (
    week_start TEXT PRIMARY KEY,
    doc_id TEXT,
    doc_url TEXT,
    draft_id TEXT,
    content_hash TEXT,
    updated_at TEXT NOT NULL
);
"""


class Database:
    """SQLite wrapper for the weekly pulse pipeline."""

    def __init__(self, db_path: Path | str = "data/pulse.db"):
        self.path = resolve_project_path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Create tables if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)

    def upsert_reviews(self, records: Iterable[ReviewRecord]) -> int:
        """Insert reviews, skipping duplicates based on review_id (idempotent ING-16).
        Returns number of newly inserted rows.
        """
        records_list = list(records)
        if not records_list:
            return 0

        query = """
        INSERT OR IGNORE INTO reviews (
            review_id, platform, rating, title, text, date,
            app_version, lang, low_info, pii_found, quote_eligible,
            raw_hash, created_at
        ) VALUES (
            :review_id, :platform, :rating, :title, :text, :date,
            :app_version, :lang, :low_info, :pii_found, :quote_eligible,
            :raw_hash, :created_at
        );
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted_count = 0
            for r in records_list:
                cursor.execute(query, r.__dict__)
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()
            return inserted_count

    def get_reviews_in_window(
        self, start_date: str, end_date: str, include_low_info: bool = True
    ) -> List[ReviewRecord]:
        """Fetch reviews within [start_date, end_date] inclusive (WIN-04)."""
        query = "SELECT * FROM reviews WHERE date >= ? AND date <= ?"
        if not include_low_info:
            query += " AND low_info = 0"
        query += " ORDER BY date ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            return [
                ReviewRecord(
                    review_id=row["review_id"],
                    platform=row["platform"],
                    rating=row["rating"],
                    title=row["title"],
                    text=row["text"],
                    date=row["date"],
                    app_version=row["app_version"],
                    lang=row["lang"],
                    low_info=row["low_info"],
                    pii_found=row["pii_found"],
                    quote_eligible=row["quote_eligible"],
                    raw_hash=row["raw_hash"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def count_reviews(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM reviews")
            return cursor.fetchone()[0]

"""SQLite database management for Groww Weekly Review Pulse.

Enforces zero identity columns (SEC-01) and idempotent insertions.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
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
    total_reviews INTEGER NOT NULL DEFAULT 0,
    analyzed_reviews INTEGER NOT NULL DEFAULT 0,
    avg_rating REAL NOT NULL DEFAULT 0.0,
    coverage_weeks REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    error TEXT,
    finished_at TEXT
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
        """Create tables if they do not exist and apply backwards-compatible migrations."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(runs)")
            existing_cols = {r["name"] for r in cursor.fetchall()}
            for col in ["window_start", "window_end", "error", "finished_at"]:
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE runs ADD COLUMN {col} TEXT;")
            conn.commit()

    def record_run_start(
        self,
        run_id: str,
        week_start: str,
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
    ) -> str:
        """Record the start of a pipeline run in runs table."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id, week_start, status, total_reviews, analyzed_reviews,
                    avg_rating, coverage_weeks, created_at, window_start, window_end
                ) VALUES (?, ?, 'running', 0, 0, 0.0, 0.0, ?, ?, ?)
                """,
                (run_id, week_start, now_iso, window_start, window_end)
            )
            conn.commit()
        return run_id

    def update_run(
        self,
        run_id: str,
        status: str,
        total_reviews: Optional[int] = None,
        analyzed_reviews: Optional[int] = None,
        avg_rating: Optional[float] = None,
        coverage_weeks: Optional[float] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        """Update run progress, metrics, or terminal status."""
        finished_at = datetime.now(timezone.utc).isoformat() if finished else None
        updates = ["status = ?"]
        params = [status]
        if total_reviews is not None:
            updates.append("total_reviews = ?")
            params.append(total_reviews)
        if analyzed_reviews is not None:
            updates.append("analyzed_reviews = ?")
            params.append(analyzed_reviews)
        if avg_rating is not None:
            updates.append("avg_rating = ?")
            params.append(avg_rating)
        if coverage_weeks is not None:
            updates.append("coverage_weeks = ?")
            params.append(coverage_weeks)
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        if finished_at is not None:
            updates.append("finished_at = ?")
            params.append(finished_at)

        params.append(run_id)
        sql = f"UPDATE runs SET {', '.join(updates)} WHERE run_id = ?"
        with self.get_connection() as conn:
            conn.execute(sql, tuple(params))
            conn.commit()

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Fetch a run by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return RunRecord(**dict(row))
        return None

    def get_active_runs(self) -> List[str]:
        """Fetch list of run_ids currently in 'running' state (ORC-08)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT run_id FROM runs WHERE status = 'running'")
            return [r[0] for r in cursor.fetchall()]

    def purge_reviews_older_than(
        self, cutoff_date: str, exclude_run_ids: Optional[List[str]] = None
    ) -> int:
        """Delete reviews with date < cutoff_date, preserving active runs (ORC-08)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if exclude_run_ids:
                placeholders = ",".join("?" for _ in exclude_run_ids)
                subquery = f"""
                    SELECT review_id FROM review_themes rt
                    JOIN themes t ON rt.theme_id = t.theme_id
                    WHERE t.run_id IN ({placeholders})
                """
                cursor.execute(
                    f"DELETE FROM reviews WHERE date < ? AND review_id NOT IN ({subquery})",
                    (cutoff_date, *exclude_run_ids),
                )
            else:
                cursor.execute("DELETE FROM reviews WHERE date < ?", (cutoff_date,))
            deleted = cursor.rowcount
            # Cleanup orphaned review_themes
            cursor.execute(
                "DELETE FROM review_themes WHERE review_id NOT IN (SELECT review_id FROM reviews)"
            )
            conn.commit()
            return deleted

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

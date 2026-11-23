import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from src.store.connectors import PostgresConnector, SqliteConnector
from src.store.errors import AppIdentityFrozen, InvalidAppRecord, UnknownApp
from src.store.models import (
    APP_STATUSES,
    AppRecord,
    CollectionRunRecord,
    PublishStateRecord,
    ReviewRecord,
    RunRecord,
    ThemeRecord,
)

Connector = Union[SqliteConnector, PostgresConnector]

REVIEW_COLUMNS = (
    "review_id", "platform", "rating", "title", "text", "date", "app_version",
    "lang", "low_info", "pii_found", "quote_eligible", "raw_hash", "created_at",
)
RUN_COLUMNS = (
    "run_id", "week_start", "status", "total_reviews", "analyzed_reviews", "avg_rating",
    "coverage_weeks", "created_at", "window_start", "window_end", "error", "finished_at",
)
APP_COLUMNS = (
    "app_key", "display_name", "play_package_id", "app_store_id", "country", "lang",
    "category", "status", "created_at", "archived_at",
)
LISTING_COLUMNS = {"play_store": "play_package_id", "app_store": "app_store_id"}
COLLECTION_COLUMNS = (
    "collection_id", "platform", "mode", "window_start", "window_end", "status", "started_at",
    "covered_start", "fetched", "inserted", "source_limit_hit", "feed_gaps", "error", "finished_at",
)
THEME_COLUMNS = (
    "theme_id", "run_id", "label", "description", "review_count", "share_pct", "avg_rating", "is_top3",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pick(row: Dict[str, Any], columns: Sequence[str]) -> Dict[str, Any]:
    return {c: row[c] for c in columns}


def _review(row: Dict[str, Any]) -> ReviewRecord:
    return ReviewRecord(**_pick(row, REVIEW_COLUMNS))


def _run(row: Dict[str, Any]) -> RunRecord:
    return RunRecord(**_pick(row, RUN_COLUMNS))


def _app(row: Dict[str, Any]) -> AppRecord:
    return AppRecord(**_pick(row, APP_COLUMNS))


def _theme(row: Dict[str, Any]) -> ThemeRecord:
    return ThemeRecord(**_pick(row, THEME_COLUMNS))


class PulseStore:
    def __init__(self, connector: Connector):
        self.connector = connector
        self.connector.apply_schema()

    @property
    def dialect(self) -> str:
        return self.connector.dialect

    def list_apps(self, statuses: Sequence[str] = APP_STATUSES) -> List[AppRecord]:
        placeholders = ", ".join("?" for _ in statuses)
        with self.connector.session() as s:
            rows = s.fetchall(
                f"SELECT * FROM apps WHERE status IN ({placeholders}) ORDER BY created_at, app_key",
                tuple(statuses),
            )
        return [_app(r) for r in rows]

    def get_app(self, app_key: str) -> AppRecord:
        with self.connector.session() as s:
            row = s.fetchone("SELECT * FROM apps WHERE app_key = ?", (app_key,))
        if row is None:
            raise UnknownApp(f"No app registered with app_key {app_key!r}.")
        return _app(row)

    def insert_app(self, app: AppRecord) -> AppRecord:
        values = _pick(app.__dict__, APP_COLUMNS)
        with self.connector.session() as s:
            s.execute(
                f"INSERT INTO apps ({', '.join(APP_COLUMNS)}) VALUES ({', '.join('?' for _ in APP_COLUMNS)})",
                tuple(values.values()),
            )
        return self.get_app(app.app_key)

    def rename_app(self, app_key: str, display_name: str) -> AppRecord:
        with self.connector.session() as s:
            changed = s.execute("UPDATE apps SET display_name = ? WHERE app_key = ?", (display_name, app_key))
        if changed == 0:
            raise UnknownApp(f"No app registered with app_key {app_key!r}.")
        return self.get_app(app_key)

    def set_app_status(self, app_key: str, status: str) -> AppRecord:
        archived_at = _now() if status == "archived" else None
        with self.connector.session() as s:
            changed = s.execute(
                "UPDATE apps SET status = ?, archived_at = ? WHERE app_key = ?",
                (status, archived_at, app_key),
            )
        if changed == 0:
            raise UnknownApp(f"No app registered with app_key {app_key!r}.")
        return self.get_app(app_key)

    def attach_listing(self, app_key: str, platform: str, listing_id: str) -> AppRecord:
        column = LISTING_COLUMNS.get(platform)
        if column is None:
            raise InvalidAppRecord(f"Unknown platform {platform!r}. Use one of {sorted(LISTING_COLUMNS)}.")
        with self.connector.session() as s:
            changed = s.execute(
                f"UPDATE apps SET {column} = ? WHERE app_key = ? AND {column} IS NULL", (listing_id, app_key)
            )
        app = self.get_app(app_key)
        if changed == 0 and getattr(app, column) != listing_id:
            raise AppIdentityFrozen(f"{app_key} already has {column}={getattr(app, column)!r}. Use replace instead.")
        return app

    def for_app(self, app_key: str) -> "AppStore":
        return AppStore(self, self.get_app(app_key))


class AppStore:
    def __init__(self, store: PulseStore, app: AppRecord):
        self._store = store
        self.app = app

    @property
    def app_key(self) -> str:
        return self.app.app_key

    @property
    def connector(self) -> Connector:
        return self._store.connector

    def set_status(self, status: str) -> AppRecord:
        self.app = self._store.set_app_status(self.app_key, status)
        return self.app

    def _session(self):
        return self._store.connector.session()

    def upsert_reviews(self, records: Iterable[ReviewRecord]) -> int:
        columns = ("app_key",) + REVIEW_COLUMNS
        sql = (
            f"INSERT INTO reviews ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) "
            "ON CONFLICT (app_key, review_id) DO NOTHING"
        )
        inserted = 0
        with self._session() as s:
            for record in records:
                values = (self.app_key,) + tuple(record.__dict__[c] for c in REVIEW_COLUMNS)
                inserted += max(s.execute(sql, values), 0)
        return inserted

    def get_reviews_in_window(
        self, start_date: str, end_date: str, include_low_info: bool = True
    ) -> List[ReviewRecord]:
        sql = "SELECT * FROM reviews WHERE app_key = ? AND date >= ? AND date <= ?"
        if not include_low_info:
            sql += " AND low_info = 0"
        sql += " ORDER BY date ASC, review_id ASC"
        with self._session() as s:
            rows = s.fetchall(sql, (self.app_key, start_date, end_date))
        return [_review(r) for r in rows]

    def count_reviews(self) -> int:
        with self._session() as s:
            return int(s.scalar("SELECT COUNT(*) AS n FROM reviews WHERE app_key = ?", (self.app_key,)))

    def record_run_start(
        self,
        run_id: str,
        week_start: str,
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
    ) -> str:
        with self._session() as s:
            s.execute(
                "INSERT INTO runs (app_key, run_id, week_start, status, created_at, window_start, window_end) "
                "VALUES (?, ?, ?, 'running', ?, ?, ?) "
                "ON CONFLICT (app_key, run_id) DO UPDATE SET status = 'running', week_start = excluded.week_start, "
                "window_start = excluded.window_start, window_end = excluded.window_end",
                (self.app_key, run_id, week_start, _now(), window_start, window_end),
            )
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
        updates: Dict[str, Any] = {"status": status}
        for name, value in (
            ("total_reviews", total_reviews),
            ("analyzed_reviews", analyzed_reviews),
            ("avg_rating", avg_rating),
            ("coverage_weeks", coverage_weeks),
            ("error", error),
        ):
            if value is not None:
                updates[name] = value
        if finished:
            updates["finished_at"] = _now()
        assignments = ", ".join(f"{k} = ?" for k in updates)
        with self._session() as s:
            s.execute(
                f"UPDATE runs SET {assignments} WHERE app_key = ? AND run_id = ?",
                tuple(updates.values()) + (self.app_key, run_id),
            )

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self._session() as s:
            row = s.fetchone("SELECT * FROM runs WHERE app_key = ? AND run_id = ?", (self.app_key, run_id))
        return _run(row) if row else None

    def get_active_run_ids(self) -> List[str]:
        with self._session() as s:
            rows = s.fetchall(
                "SELECT run_id FROM runs WHERE app_key = ? AND status = 'running'", (self.app_key,)
            )
        return [r["run_id"] for r in rows]

    def latest_themed_run_for_week(self, week_start: str) -> Optional[RunRecord]:
        sql = (
            "SELECT r.* FROM runs r WHERE r.app_key = ? AND r.week_start = ? "
            "AND EXISTS (SELECT 1 FROM themes t WHERE t.app_key = r.app_key AND t.run_id = r.run_id) "
            "ORDER BY r.created_at DESC LIMIT 1"
        )
        with self._session() as s:
            row = s.fetchone(sql, (self.app_key, week_start))
        return _run(row) if row else None

    def save_theme_run(
        self,
        run_id: str,
        week_start: str,
        total_reviews: int,
        analyzed_reviews: int,
        avg_rating: float,
        coverage_weeks: float,
        themes: List[Dict[str, Any]],
    ) -> None:
        theme_upsert = (
            f"INSERT INTO themes (app_key, {', '.join(THEME_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in range(len(THEME_COLUMNS) + 1))}) "
            "ON CONFLICT (app_key, theme_id) DO UPDATE SET run_id = excluded.run_id, label = excluded.label, "
            "description = excluded.description, review_count = excluded.review_count, "
            "share_pct = excluded.share_pct, avg_rating = excluded.avg_rating, is_top3 = excluded.is_top3"
        )
        with self._session() as s:
            s.execute(
                "INSERT INTO runs (app_key, run_id, week_start, status, total_reviews, analyzed_reviews, "
                "avg_rating, coverage_weeks, created_at) VALUES (?, ?, ?, 'themes_completed', ?, ?, ?, ?, ?) "
                "ON CONFLICT (app_key, run_id) DO UPDATE SET status = excluded.status, "
                "total_reviews = excluded.total_reviews, analyzed_reviews = excluded.analyzed_reviews, "
                "avg_rating = excluded.avg_rating, coverage_weeks = excluded.coverage_weeks",
                (self.app_key, run_id, week_start, total_reviews, analyzed_reviews, avg_rating,
                 coverage_weeks, _now()),
            )
            for theme in themes:
                s.execute(
                    "DELETE FROM review_themes WHERE app_key = ? AND theme_id = ?",
                    (self.app_key, theme["theme_id"]),
                )
                s.execute(
                    theme_upsert,
                    (self.app_key, theme["theme_id"], run_id, theme["label"], theme["description"],
                     theme["review_count"], theme["share_pct"], theme["avg_rating"], theme["is_top3"]),
                )
                for review_id in theme["member_review_ids"]:
                    s.execute(
                        "INSERT INTO review_themes (app_key, review_id, theme_id, distance) VALUES (?, ?, ?, 0.0) "
                        "ON CONFLICT (app_key, review_id, theme_id) DO NOTHING",
                        (self.app_key, review_id, theme["theme_id"]),
                    )

    def get_themes(self, run_id: str) -> List[ThemeRecord]:
        with self._session() as s:
            rows = s.fetchall(
                "SELECT * FROM themes WHERE app_key = ? AND run_id = ? ORDER BY is_top3 DESC, share_pct DESC",
                (self.app_key, run_id),
            )
        return [_theme(r) for r in rows]

    def get_theme_reviews(self, run_id: str) -> Dict[str, List[ReviewRecord]]:
        sql = (
            "SELECT r.*, rt.theme_id AS assigned_theme_id FROM reviews r "
            "JOIN review_themes rt ON rt.app_key = r.app_key AND rt.review_id = r.review_id "
            "JOIN themes t ON t.app_key = rt.app_key AND t.theme_id = rt.theme_id "
            "WHERE r.app_key = ? AND t.run_id = ? ORDER BY r.date ASC, r.review_id ASC"
        )
        grouped: Dict[str, List[ReviewRecord]] = {}
        with self._session() as s:
            for row in s.fetchall(sql, (self.app_key, run_id)):
                grouped.setdefault(row["assigned_theme_id"], []).append(_review(row))
        return grouped

    def get_publish_state(self, week_start: str) -> Optional[PublishStateRecord]:
        with self._session() as s:
            row = s.fetchone(
                "SELECT * FROM publish_state WHERE app_key = ? AND week_start = ?", (self.app_key, week_start)
            )
        if row is None:
            return None
        return PublishStateRecord(
            week_start=row["week_start"], doc_id=row["doc_id"], doc_url=row["doc_url"],
            draft_id=row["draft_id"], content_hash=row["content_hash"], updated_at=row["updated_at"],
        )

    def count_publish_states(self) -> int:
        with self._session() as s:
            return int(s.scalar("SELECT COUNT(*) AS n FROM publish_state WHERE app_key = ?", (self.app_key,)))

    def save_publish_state(self, state: PublishStateRecord) -> None:
        with self._session() as s:
            s.execute(
                "INSERT INTO publish_state (app_key, week_start, doc_id, doc_url, draft_id, content_hash, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (app_key, week_start) DO UPDATE SET "
                "doc_id = excluded.doc_id, doc_url = excluded.doc_url, draft_id = excluded.draft_id, "
                "content_hash = excluded.content_hash, updated_at = excluded.updated_at",
                (self.app_key, state.week_start, state.doc_id, state.doc_url, state.draft_id,
                 state.content_hash, _now()),
            )

    def get_cached_embeddings(self, model_name: str, review_ids: List[str]) -> Dict[str, List[float]]:
        if not review_ids:
            return {}
        placeholders = ", ".join("?" for _ in review_ids)
        with self._session() as s:
            rows = s.fetchall(
                f"SELECT review_id, vector_json FROM embedding_cache WHERE app_key = ? AND model_name = ? "
                f"AND review_id IN ({placeholders})",
                (self.app_key, model_name, *review_ids),
            )
        return {r["review_id"]: json.loads(r["vector_json"]) for r in rows}

    def save_cached_embeddings(self, model_name: str, items: List[Tuple[str, List[float]]]) -> None:
        with self._session() as s:
            for review_id, vector in items:
                s.execute(
                    "INSERT INTO embedding_cache (app_key, review_id, model_name, vector_json) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT (app_key, review_id, model_name) DO UPDATE SET vector_json = excluded.vector_json",
                    (self.app_key, review_id, model_name, json.dumps(vector)),
                )

    def cached_embedding_models(self) -> List[str]:
        with self._session() as s:
            rows = s.fetchall(
                "SELECT DISTINCT model_name FROM embedding_cache WHERE app_key = ? ORDER BY model_name",
                (self.app_key,),
            )
        return [r["model_name"] for r in rows]

    def purge_reviews_older_than(self, cutoff_date: str, exclude_run_ids: Optional[List[str]] = None) -> int:
        protected = list(exclude_run_ids or [])
        protected_clause = ""
        params: Tuple[Any, ...] = (self.app_key, cutoff_date)
        if protected:
            placeholders = ", ".join("?" for _ in protected)
            protected_clause = (
                " AND review_id NOT IN (SELECT rt.review_id FROM review_themes rt "
                "JOIN themes t ON t.app_key = rt.app_key AND t.theme_id = rt.theme_id "
                f"WHERE rt.app_key = ? AND t.run_id IN ({placeholders}))"
            )
            params = params + (self.app_key, *protected)
        purge_targets = f"SELECT review_id FROM reviews WHERE app_key = ? AND date < ?{protected_clause}"
        with self._session() as s:
            s.execute(
                f"DELETE FROM embedding_cache WHERE app_key = ? AND review_id IN ({purge_targets})",
                (self.app_key,) + params,
            )
            s.execute(
                f"DELETE FROM review_themes WHERE app_key = ? AND review_id IN ({purge_targets})",
                (self.app_key,) + params,
            )
            deleted = s.execute(
                f"DELETE FROM reviews WHERE app_key = ? AND date < ?{protected_clause}", params
            )
        return deleted

    def start_collection(self, platform: str, mode: str, window_start: str, window_end: str) -> int:
        with self._session() as s:
            row = s.fetchone(
                "INSERT INTO collection_runs (app_key, platform, mode, window_start, window_end, status, started_at) "
                "VALUES (?, ?, ?, ?, ?, 'running', ?) RETURNING collection_id",
                (self.app_key, platform, mode, window_start, window_end, _now()),
            )
        return int(row["collection_id"])

    def finish_collection(
        self,
        collection_id: int,
        status: str,
        fetched: int = 0,
        inserted: int = 0,
        covered_start: Optional[str] = None,
        source_limit_hit: bool = False,
        feed_gaps: int = 0,
        error: Optional[str] = None,
    ) -> CollectionRunRecord:
        with self._session() as s:
            changed = s.execute(
                "UPDATE collection_runs SET status = ?, fetched = ?, inserted = ?, covered_start = ?, "
                "source_limit_hit = ?, feed_gaps = ?, error = ?, finished_at = ? "
                "WHERE app_key = ? AND collection_id = ?",
                (status, fetched, inserted, covered_start, int(source_limit_hit), feed_gaps, error, _now(),
                 self.app_key, collection_id),
            )
        if changed == 0:
            raise KeyError(f"No collection run {collection_id} for app {self.app_key!r}.")
        return self.get_collection(collection_id)

    def record_skipped_collection(self, platform: str, mode: str, window_start: str, window_end: str) -> CollectionRunRecord:
        collection_id = self.start_collection(platform, mode, window_start, window_end)
        return self.finish_collection(collection_id, "skipped_disabled")

    def get_collection(self, collection_id: int) -> CollectionRunRecord:
        with self._session() as s:
            row = s.fetchone(
                "SELECT * FROM collection_runs WHERE app_key = ? AND collection_id = ?",
                (self.app_key, collection_id),
            )
        return CollectionRunRecord(**_pick(row, COLLECTION_COLUMNS))

    def list_collections(self) -> List[CollectionRunRecord]:
        with self._session() as s:
            rows = s.fetchall(
                "SELECT * FROM collection_runs WHERE app_key = ? ORDER BY collection_id",
                (self.app_key,),
            )
        return [CollectionRunRecord(**_pick(r, COLLECTION_COLUMNS)) for r in rows]

    def latest_finished_collection(self, platform: str) -> Optional[CollectionRunRecord]:
        with self._session() as s:
            row = s.fetchone(
                "SELECT * FROM collection_runs WHERE app_key = ? AND platform = ? AND status <> 'running' "
                "ORDER BY collection_id DESC LIMIT 1",
                (self.app_key, platform),
            )
        return None if row is None else CollectionRunRecord(**_pick(row, COLLECTION_COLUMNS))

    def platform_counts(self, window_start: str, window_end: str) -> Dict[str, int]:
        with self._session() as s:
            rows = s.fetchall(
                "SELECT platform, COUNT(*) AS n FROM reviews WHERE app_key = ? AND date >= ? AND date <= ? "
                "GROUP BY platform",
                (self.app_key, window_start, window_end),
            )
        return {r["platform"]: int(r["n"]) for r in rows}

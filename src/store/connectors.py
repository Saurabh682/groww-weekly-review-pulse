import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence

from src.store.errors import translate_integrity_error

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SQLITE_SCHEMA_FILE = SCHEMA_DIR / "sqlite.sql"
POSTGRES_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
SQLITE_SCHEMA_VERSION = 4
MIGRATION_LOCK_KEY = 4207311


class SqlSession:
    def __init__(self, raw_connection: Any, placeholder: str):
        self._conn = raw_connection
        self._placeholder = placeholder

    def _sql(self, sql: str) -> str:
        return sql if self._placeholder == "?" else sql.replace("?", self._placeholder)

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        cursor = self._conn.cursor()
        cursor.execute(self._sql(sql), tuple(params))
        return cursor.rowcount

    def fetchone(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(self._sql(sql), tuple(params))
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(self._sql(sql), tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def scalar(self, sql: str, params: Sequence[Any] = ()) -> Any:
        row = self.fetchone(sql, params)
        return None if row is None else next(iter(row.values()))


class SharedReads:
    placeholder: str

    def __init__(self) -> None:
        self._held = threading.local()

    def _connect_read_only(self) -> Any:
        raise NotImplementedError

    @property
    def _shared(self) -> Optional[SqlSession]:
        return getattr(self._held, "session", None)

    @contextmanager
    def reading(self) -> Iterator[None]:
        if self._shared is not None:
            yield
            return
        conn = self._connect_read_only()
        self._held.session = SqlSession(conn, self.placeholder)
        try:
            yield
        finally:
            self._held.session = None
            conn.close()


class SqliteConnector(SharedReads):
    dialect = "sqlite"
    placeholder = "?"

    def __init__(self, path: Path):
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _connect_read_only(self) -> sqlite3.Connection:
        conn = self._connect()
        conn.execute("PRAGMA query_only = ON;")
        return conn

    @contextmanager
    def session(self) -> Iterator[SqlSession]:
        if self._shared is not None:
            yield self._shared
            return
        conn = self._connect()
        try:
            yield SqlSession(conn, self.placeholder)
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise translate_integrity_error(exc) from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def apply_schema(self) -> None:
        conn = sqlite3.connect(str(self.path))
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            legacy = _sqlite_has_legacy_v1_schema(conn)
            scores_missing = "themes" in _sqlite_tables(conn) and "neg_share" not in _sqlite_columns(conn, "themes")
            if legacy:
                _sqlite_rename_legacy_tables(conn)
            if "collection_runs" in _sqlite_tables(conn) and "feed_gaps" not in _sqlite_columns(conn, "collection_runs"):
                conn.execute("ALTER TABLE collection_runs ADD COLUMN feed_gaps INTEGER NOT NULL DEFAULT 0")
            if scores_missing and not legacy:
                _sqlite_add_theme_score_columns(conn)
            conn.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))
            if legacy:
                _sqlite_copy_legacy_rows(conn)
            if scores_missing:
                _sqlite_fill_theme_scores(conn)
            if version != SQLITE_SCHEMA_VERSION:
                conn.execute(f"PRAGMA user_version = {SQLITE_SCHEMA_VERSION}")
            conn.commit()
        finally:
            conn.close()


class PostgresConnector(SharedReads):
    dialect = "postgres"
    placeholder = "%s"

    def __init__(self, dsn: str):
        super().__init__()
        self.dsn = dsn

    def _connect(self) -> Any:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.dsn, row_factory=dict_row, prepare_threshold=None)

    def _connect_read_only(self) -> Any:
        conn = self._connect()
        conn.read_only = True
        return conn

    @contextmanager
    def session(self) -> Iterator[SqlSession]:
        import psycopg

        if self._shared is not None:
            yield self._shared
            return
        conn = self._connect()
        try:
            yield SqlSession(conn, self.placeholder)
            conn.commit()
        except psycopg.errors.IntegrityError as exc:
            conn.rollback()
            raise translate_integrity_error(exc) from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def apply_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))
            conn.execute("CREATE SCHEMA IF NOT EXISTS pulse_internal")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS pulse_internal.applied_migrations "
                "(name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            applied = {r["name"] for r in conn.execute("SELECT name FROM pulse_internal.applied_migrations")}
            for migration in sorted(POSTGRES_MIGRATIONS_DIR.glob("*.sql")):
                if migration.name not in applied:
                    conn.execute(migration.read_text(encoding="utf-8"))
                    conn.execute("INSERT INTO pulse_internal.applied_migrations (name) VALUES (%s)", (migration.name,))
            conn.commit()
        finally:
            conn.close()


LEGACY_TABLES = ("reviews", "runs", "themes", "review_themes", "publish_state", "embedding_cache")


def _sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]


def _sqlite_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _sqlite_has_legacy_v1_schema(conn: sqlite3.Connection) -> bool:
    columns = _sqlite_columns(conn, "reviews")
    return bool(columns) and "app_key" not in columns


def _sqlite_rename_legacy_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in LEGACY_TABLES:
        if _sqlite_columns(conn, table):
            conn.execute(f"ALTER TABLE {table} RENAME TO legacy_v1_{table}")
    for index in ("idx_reviews_date", "idx_reviews_platform_date", "idx_reviews_low_info"):
        conn.execute(f"DROP INDEX IF EXISTS {index}")


def _sqlite_add_theme_score_columns(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE themes ADD COLUMN neg_share REAL NOT NULL DEFAULT 0.0")
    conn.execute("ALTER TABLE themes ADD COLUMN priority_score REAL NOT NULL DEFAULT 0.0")


def _sqlite_fill_theme_scores(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE themes SET neg_share = COALESCE((SELECT ROUND(AVG(CASE WHEN r.rating <= 2 THEN 1.0 ELSE 0.0 END), 4) "
        "FROM review_themes rt JOIN reviews r ON r.app_key = rt.app_key AND r.review_id = rt.review_id "
        "WHERE rt.app_key = themes.app_key AND rt.theme_id = themes.theme_id), 0.0)"
    )
    conn.execute("UPDATE themes SET priority_score = ROUND(share_pct * (0.6 + 0.4 * neg_share), 5)")


def _sqlite_copy_legacy_rows(conn: sqlite3.Connection) -> None:
    for table in LEGACY_TABLES:
        legacy = f"legacy_v1_{table}"
        legacy_columns = _sqlite_columns(conn, legacy)
        if not legacy_columns:
            continue
        target_columns = set(_sqlite_columns(conn, table))
        shared = [c for c in legacy_columns if c in target_columns]
        column_list = ", ".join(shared)
        conn.execute(
            f"INSERT OR IGNORE INTO {table} (app_key, {column_list}) "
            f"SELECT 'groww', {column_list} FROM {legacy}"
        )
        conn.execute(f"DROP TABLE {legacy}")
    conn.execute("PRAGMA foreign_keys = ON")

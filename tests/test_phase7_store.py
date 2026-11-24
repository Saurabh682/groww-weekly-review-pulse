import os
import re
import sqlite3
import uuid
from pathlib import Path

import pytest

from src.store.errors import (
    ActiveAppCapReached,
    AppIdentityFrozen,
    DuplicateStoreListing,
    InvalidAppRecord,
    UnknownApp,
)
from src.store.connectors import SQLITE_SCHEMA_VERSION
from src.store.factory import postgres_store, sqlite_store
from src.store.models import AppRecord, ReviewRecord

ROOT = Path(__file__).resolve().parents[1]
POSTGRES_DSN_ENV = "PULSE_TEST_POSTGRES_DSN"
BACKENDS = ["sqlite", "postgres"]


def _fresh_postgres_dsn() -> str:
    import psycopg
    from psycopg.conninfo import make_conninfo

    base = os.environ[POSTGRES_DSN_ENV]
    name = f"pulse_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(base, autocommit=True) as conn:
        conn.execute(f"CREATE DATABASE {name}")
    return make_conninfo(base, dbname=name)


@pytest.fixture(params=BACKENDS)
def store(request, tmp_path):
    if request.param == "sqlite":
        return sqlite_store(tmp_path / "phase7.db")
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    return postgres_store(_fresh_postgres_dsn())


def _app(key: str, **kw) -> AppRecord:
    defaults = dict(display_name=key.title(), status="active", play_package_id=f"com.example.{key}")
    defaults.update(kw)
    return AppRecord(app_key=key, **defaults)


def _review(review_id: str, text: str = "Works fine") -> ReviewRecord:
    return ReviewRecord(review_id=review_id, platform="play_store", rating=4, text=text,
                        date="2026-11-16", raw_hash=f"h-{review_id}-{text}")


def test_groww_seeded(store):
    groww = store.get_app("groww")
    assert groww.status == "active"
    assert groww.category == "Finance"
    assert groww.play_package_id == "com.nextbillion.groww"
    assert groww.app_store_id == "1404871703"


def test_app01_sixth_active_app_rejected(store):
    for i in range(4):
        store.insert_app(_app(f"app{i}"))
    with pytest.raises(ActiveAppCapReached):
        store.insert_app(_app("app4"))
    assert len(store.list_apps(("active",))) == 5


def test_app01_unarchive_respects_cap(store):
    for i in range(4):
        store.insert_app(_app(f"app{i}"))
    store.set_app_status("app0", "archived")
    store.insert_app(_app("app4"))
    with pytest.raises(ActiveAppCapReached):
        store.set_app_status("app0", "active")


def test_app05_identity_frozen(store):
    store.insert_app(_app("swiggy"))
    with pytest.raises(AppIdentityFrozen):
        with store.connector.session() as s:
            s.execute("UPDATE apps SET play_package_id = 'com.other' WHERE app_key = 'swiggy'")
    with pytest.raises(AppIdentityFrozen):
        with store.connector.session() as s:
            s.execute("UPDATE apps SET app_key = 'swiggy2' WHERE app_key = 'swiggy'")
    assert store.rename_app("swiggy", "Swiggy Food").display_name == "Swiggy Food"


def test_app06_needs_a_store_listing(store):
    with pytest.raises(InvalidAppRecord):
        store.insert_app(_app("nolisting", play_package_id=None, app_store_id=None))


def test_app_status_must_be_known(store):
    with pytest.raises(InvalidAppRecord):
        store.insert_app(_app("weird", status="paused"))


def test_duplicate_live_listing_rejected_but_archived_reusable(store):
    store.insert_app(_app("zomato"))
    with pytest.raises(DuplicateStoreListing):
        store.insert_app(_app("zomato2", play_package_id="com.example.zomato"))
    store.set_app_status("zomato", "archived")
    store.insert_app(_app("zomato2", play_package_id="com.example.zomato"))


def test_unknown_app_raises(store):
    with pytest.raises(UnknownApp):
        store.for_app("nope")
    with pytest.raises(UnknownApp):
        store.rename_app("nope", "Nope")


def test_sto02_reviews_scoped_by_app(store):
    store.insert_app(_app("swiggy"))
    groww = store.for_app("groww")
    swiggy = store.for_app("swiggy")
    groww.upsert_reviews([_review("r1", "groww text"), _review("r2")])
    swiggy.upsert_reviews([_review("r1", "swiggy text")])
    assert groww.count_reviews() == 2
    assert swiggy.count_reviews() == 1
    swiggy_texts = [r.text for r in swiggy.get_reviews_in_window("2026-11-01", "2026-11-30")]
    assert swiggy_texts == ["swiggy text"]


def test_sto05_schema_apply_is_idempotent(store):
    store.insert_app(_app("swiggy"))
    store.for_app("swiggy").upsert_reviews([_review("r1")])
    store.connector.apply_schema()
    store.connector.apply_schema()
    assert len(store.list_apps()) == 2
    assert store.for_app("swiggy").count_reviews() == 1


def test_postgres_rls_enabled_on_every_table(store):
    if store.dialect != "postgres":
        pytest.skip("RLS exists only on Postgres")
    with store.connector.session() as s:
        rows = s.fetchall(
            "SELECT relname, relrowsecurity FROM pg_class "
            "WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace"
        )
    assert rows
    assert all(r["relrowsecurity"] for r in rows), rows


def _sqlite_columns(path: Path) -> dict:
    conn = sqlite3.connect(path)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    result = {t: sorted(r[1] for r in conn.execute(f"PRAGMA table_info({t})")) for t in tables}
    conn.close()
    return result


def test_sto01_sqlite_and_postgres_schemas_match(tmp_path):
    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    sqlite_store(tmp_path / "parity.db")
    pg = postgres_store(_fresh_postgres_dsn())
    with pg.connector.session() as s:
        rows = s.fetchall(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"
        )
    pg_columns: dict = {}
    for r in rows:
        pg_columns.setdefault(r["table_name"], []).append(r["column_name"])
    assert {t: sorted(c) for t, c in pg_columns.items()} == _sqlite_columns(tmp_path / "parity.db")


LEGACY_V1_SCHEMA = (ROOT / "tests" / "fixtures" / "legacy_v1_schema.sql").read_text(encoding="utf-8")
LEGACY_ROW = (
    "INSERT INTO reviews (review_id, platform, rating, text, date, raw_hash, created_at) "
    "VALUES ('legacy1', 'play_store', 5, 'Great', '2026-11-10', 'h1', '2026-11-11')"
)


def test_legacy_v1_database_migrates_into_groww(tmp_path):
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.executescript(LEGACY_V1_SCHEMA)
    conn.execute(LEGACY_ROW)
    conn.commit()
    conn.close()
    groww = sqlite_store(path).for_app("groww")
    assert groww.count_reviews() == 1
    assert groww.get_reviews_in_window("2026-11-01", "2026-11-30")[0].review_id == "legacy1"
    conn = sqlite3.connect(path)
    leftovers = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE name LIKE '%legacy%'")]
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    conn.close()
    assert leftovers == []
    assert version == SQLITE_SCHEMA_VERSION


APP_NAME_PATTERN = re.compile(r"\b(groww|zerodha|swiggy|zomato|phonepe|paytm)\b", re.IGNORECASE)


def test_prompts_contain_no_app_names():
    offenders = [p.name for p in (ROOT / "prompts").glob("**/*") if p.is_file()
                 and APP_NAME_PATTERN.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


def test_generic_pack_contains_no_app_names():
    from src.domains.generic import GENERIC_PACK

    assert not APP_NAME_PATTERN.search(repr(GENERIC_PACK))


def test_APP_02_concurrent_inserts_respect_cap(store):
    import threading

    for i in range(3):
        store.insert_app(_app(f"app{i}"))
    barrier = threading.Barrier(4)
    outcomes = []

    def add(key):
        barrier.wait()
        try:
            store.insert_app(_app(key))
            outcomes.append("ok")
        except ActiveAppCapReached:
            outcomes.append("cap")

    threads = [threading.Thread(target=add, args=(f"race{i}",)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == ["cap", "cap", "cap", "ok"]
    assert len(store.list_apps(("active",))) == 5


CLIENT_ROLES = ("anon", "authenticated")
DEFAULT_GRANT = "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON {} TO anon, authenticated"
CLIENT_WRITE = ("INSERT INTO apps (app_key, display_name, app_store_id, status, created_at) "
                "VALUES ('probe', 'Probe', '1', 'archived', '2026-11-24')")


@pytest.fixture
def supabase_like_dsn():
    import psycopg

    if POSTGRES_DSN_ENV not in os.environ:
        pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
    dsn = _fresh_postgres_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        for role in CLIENT_ROLES:
            conn.execute(f"CREATE ROLE {role} NOLOGIN")
        for kind in ("TABLES", "SEQUENCES", "FUNCTIONS"):
            conn.execute(DEFAULT_GRANT.format(kind))
    yield dsn
    with psycopg.connect(dsn, autocommit=True) as conn:
        for role in CLIENT_ROLES:
            conn.execute(f"DROP OWNED BY {role}")
            conn.execute(f"DROP ROLE {role}")


def _public_tables(conn) -> list:
    return [r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1")]


def _client_denied(conn, role: str, statement: str) -> bool:
    import psycopg

    try:
        with conn.transaction():
            conn.execute(f"SET LOCAL ROLE {role}")
            conn.execute(statement)
    except psycopg.errors.InsufficientPrivilege:
        return True
    return False


@pytest.mark.parametrize("role", CLIENT_ROLES)
def test_STO_03_client_roles_hold_no_privileges(supabase_like_dsn, role):
    import psycopg

    postgres_store(supabase_like_dsn)
    with psycopg.connect(supabase_like_dsn, autocommit=True) as conn:
        conn.execute("CREATE TABLE added_later (id BIGSERIAL PRIMARY KEY)")
        conn.execute("CREATE FUNCTION added_later_fn() RETURNS INT LANGUAGE sql AS 'SELECT 1'")
        conn.execute("REVOKE EXECUTE ON FUNCTION added_later_fn() FROM PUBLIC")
        tables = _public_tables(conn)
        assert {"apps", "reviews", "publish_state", "added_later"} <= set(tables)
        for table in tables:
            for statement in (f"SELECT * FROM {table}", f"DELETE FROM {table}", f"TRUNCATE {table} CASCADE"):
                assert _client_denied(conn, role, statement), (role, statement)
        assert _client_denied(conn, role, CLIENT_WRITE)
        sequences = conn.execute("SELECT c.oid FROM pg_class c WHERE c.relkind = 'S' "
                                 "AND c.relnamespace = 'public'::regnamespace").fetchall()
        functions = conn.execute("SELECT p.oid FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace").fetchall()
        assert len(sequences) == 2 and len(functions) == 3
        for (oid,) in sequences:
            assert not conn.execute("SELECT has_sequence_privilege(%s, %s::oid, 'USAGE')", (role, oid)).fetchone()[0]
        for (oid,) in functions:
            assert not conn.execute("SELECT has_function_privilege(%s, %s::oid, 'EXECUTE')", (role, oid)).fetchone()[0]


@pytest.mark.parametrize("role", CLIENT_ROLES)
def test_STO_03_rls_denies_anon(supabase_like_dsn, role):
    import psycopg

    store = postgres_store(supabase_like_dsn)
    store.for_app("groww").upsert_reviews([_review("r1")])
    with psycopg.connect(supabase_like_dsn, autocommit=True) as conn:
        conn.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        conn.execute(f"GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO {role}")
        assert conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 1
        for table in _public_tables(conn):
            with conn.transaction():
                conn.execute(f"SET LOCAL ROLE {role}")
                assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, (role, table)
        assert _client_denied(conn, role, CLIENT_WRITE)


def test_STO_03_triggers_still_work_without_client_privileges(supabase_like_dsn):
    store = postgres_store(supabase_like_dsn)
    for i in range(4):
        store.insert_app(_app(f"app{i}"))
    with pytest.raises(ActiveAppCapReached):
        store.insert_app(_app("app4"))

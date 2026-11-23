import os
from pathlib import Path
from typing import Optional

from src.config import get_project_root
from src.store.connectors import PostgresConnector, SqliteConnector
from src.store.store import PulseStore

DEFAULT_SQLITE_PATH = Path("data") / "pulse.db"
STORE_BACKENDS = ("sqlite", "supabase")


def sqlite_store(path: Path | str) -> PulseStore:
    return PulseStore(SqliteConnector(Path(path)))


def postgres_store(dsn: str) -> PulseStore:
    return PulseStore(PostgresConnector(dsn))


def open_store(backend: Optional[str] = None) -> PulseStore:
    selected = backend or os.getenv("PULSE_STORE", "sqlite")
    if selected == "sqlite":
        return sqlite_store(get_project_root() / DEFAULT_SQLITE_PATH)
    if selected == "supabase":
        dsn = os.getenv("SUPABASE_DB_URL")
        if not dsn:
            raise ValueError("PULSE_STORE=supabase requires the SUPABASE_DB_URL environment variable.")
        return postgres_store(dsn)
    raise ValueError(f"PULSE_STORE must be one of {STORE_BACKENDS}, got {selected!r}.")

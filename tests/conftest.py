import pytest

from src.store.factory import sqlite_store
from src.store.store import AppStore, PulseStore

TEST_RECIPIENT = "pulse-test@example.com"


@pytest.fixture(autouse=True)
def _draft_recipient(monkeypatch):
    monkeypatch.setenv("PULSE_EMAIL_TO", TEST_RECIPIENT)


@pytest.fixture
def pulse_store(tmp_path) -> PulseStore:
    return sqlite_store(tmp_path / "pulse_test.db")


@pytest.fixture
def groww_store(pulse_store) -> AppStore:
    return pulse_store.for_app("groww")

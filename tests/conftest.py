import pytest

from src.config import PROJECT_ROOT, RUNTIME_ROOT_ENV
from src.store.factory import sqlite_store
from src.store.store import AppStore, PulseStore

TEST_RECIPIENT = "pulse-test@example.com"
PROTECTED_DIRS = ("data", "outputs")
FINGERPRINT_KEY = pytest.StashKey[dict]()
CHANGED_KEY = pytest.StashKey[list]()


def runtime_file_fingerprint(root=PROJECT_ROOT) -> dict:
    files = (p for name in PROTECTED_DIRS for p in (root / name).rglob("*") if p.is_file())
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size) for p in files}


def changed_files(before: dict, after: dict) -> list:
    return sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))


def pytest_sessionstart(session):
    session.config.stash[FINGERPRINT_KEY] = runtime_file_fingerprint()


def pytest_sessionfinish(session, exitstatus):
    changed = changed_files(session.config.stash[FINGERPRINT_KEY], runtime_file_fingerprint())
    session.config.stash[CHANGED_KEY] = changed
    if changed:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter, config):
    changed = config.stash.get(CHANGED_KEY, [])
    if changed:
        terminalreporter.section("project files changed during the test run")
        terminalreporter.write_line("Tests must write under PULSE_HOME, never in data/ or outputs/.")
        for path in changed:
            terminalreporter.write_line(f"  {path}")


@pytest.fixture(autouse=True)
def _isolated_runtime_root(monkeypatch, tmp_path_factory):
    monkeypatch.setenv(RUNTIME_ROOT_ENV, str(tmp_path_factory.mktemp("pulse_home")))


@pytest.fixture(autouse=True)
def _draft_recipient(monkeypatch):
    monkeypatch.setenv("PULSE_EMAIL_TO", TEST_RECIPIENT)


@pytest.fixture
def pulse_store(tmp_path) -> PulseStore:
    return sqlite_store(tmp_path / "pulse_test.db")


@pytest.fixture
def groww_store(pulse_store) -> AppStore:
    return pulse_store.for_app("groww")


@pytest.fixture
def composio():
    from tests.support.composio_server import FakeComposio

    server = FakeComposio().start()
    yield server
    server.stop()

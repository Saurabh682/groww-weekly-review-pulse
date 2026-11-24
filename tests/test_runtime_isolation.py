import re

from src.config import (
    PROJECT_ROOT,
    RUNTIME_ROOT_ENV,
    default_sqlite_path,
    outputs_root,
    raw_reviews_dir,
    runtime_root,
)
from src.store.factory import open_store
from tests.conftest import changed_files, runtime_file_fingerprint

HARDCODED_RUNTIME_DIR = re.compile(r"""/\s*["'](?:outputs|data)\b|Path\(["'](?:outputs|data)\b""")


def test_every_default_location_is_outside_the_project():
    for path in (runtime_root(), outputs_root(), raw_reviews_dir("groww"), default_sqlite_path()):
        assert not path.is_relative_to(PROJECT_ROOT) or path.is_relative_to(PROJECT_ROOT / ".pytest_tmp")


def test_default_store_is_isolated(monkeypatch):
    monkeypatch.delenv("PULSE_STORE", raising=False)
    open_store()
    assert default_sqlite_path().is_file()


def test_unset_runtime_root_is_the_project(monkeypatch):
    monkeypatch.delenv(RUNTIME_ROOT_ENV)
    assert runtime_root() == PROJECT_ROOT
    assert default_sqlite_path() == PROJECT_ROOT / "data" / "pulse.db"


def test_only_config_builds_runtime_paths():
    offenders = [
        f"{p.relative_to(PROJECT_ROOT)}: {line.strip()}"
        for p in (PROJECT_ROOT / "src").rglob("*.py")
        if p.name != "config.py"
        for line in p.read_text(encoding="utf-8").splitlines()
        if HARDCODED_RUNTIME_DIR.search(line)
    ]
    assert offenders == [], "Runtime paths are banned here. Use outputs_root, raw_reviews_dir or default_sqlite_path."


def test_fingerprint_detects_add_edit_and_delete(tmp_path):
    (tmp_path / "data").mkdir()
    kept, gone = tmp_path / "data" / "kept.txt", tmp_path / "data" / "gone.txt"
    kept.write_text("a", encoding="utf-8")
    gone.write_text("a", encoding="utf-8")
    before = runtime_file_fingerprint(tmp_path)
    kept.write_text("edited", encoding="utf-8")
    gone.unlink()
    (tmp_path / "data" / "new.txt").write_text("n", encoding="utf-8")
    assert changed_files(before, runtime_file_fingerprint(tmp_path)) == ["data/gone.txt", "data/kept.txt", "data/new.txt"]

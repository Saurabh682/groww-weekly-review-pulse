import filecmp
import re
import subprocess
from pathlib import Path

from scripts.build_hf_space import PROJECT_ROOT, build_hf_space

SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[0-9a-f]{24,}", re.IGNORECASE),
    re.compile(r"\b[0-9a-f]{48}\b"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
)
SCANNED_SUFFIXES = {".py", ".yaml", ".yml", ".toml", ".json", ".md", ".ts", ".tsx", ".sql", ".example"}


def _tracked_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [PROJECT_ROOT / line for line in listing]


def _dirs_identical(left: Path, right: Path) -> bool:
    comparison = filecmp.dircmp(left, right, ignore=["__pycache__"])
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    return all(_dirs_identical(left / sub, right / sub) for sub in comparison.common_dirs)


def test_no_hf_space_src_copy_tracked():
    tracked = [p for p in _tracked_files() if p.relative_to(PROJECT_ROOT).parts[0] == "hf_space"]
    assert tracked == []


def test_hf_space_build_mirrors_root_src(tmp_path):
    build_dir = build_hf_space(tmp_path / "space")
    assert (build_dir / "app.py").exists()
    assert _dirs_identical(PROJECT_ROOT / "src", build_dir / "src")


def test_no_secrets_in_tracked_files():
    hits = []
    for path in _tracked_files():
        if path.suffix not in SCANNED_SUFFIXES or not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{path.relative_to(PROJECT_ROOT)}: {pattern.pattern}")
    assert hits == []

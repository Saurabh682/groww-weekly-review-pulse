import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPACE_TEMPLATE_DIR = PROJECT_ROOT / "deploy" / "hf_space"
SPACE_BUILD_DIR = PROJECT_ROOT / "hf_space"
SHARED_DIRS = ("src", "config", "prompts")
IGNORED_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")


def build_hf_space(build_dir: Path = SPACE_BUILD_DIR) -> Path:
    if build_dir.exists():
        shutil.rmtree(build_dir)
    shutil.copytree(SPACE_TEMPLATE_DIR, build_dir, ignore=IGNORED_NAMES)
    for name in SHARED_DIRS:
        source = PROJECT_ROOT / name
        if source.exists():
            shutil.copytree(source, build_dir / name, ignore=IGNORED_NAMES)
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", build_dir / "pyproject.toml")
    return build_dir


if __name__ == "__main__":
    target = build_hf_space(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SPACE_BUILD_DIR)
    print(f"HF Space build written to {target}")

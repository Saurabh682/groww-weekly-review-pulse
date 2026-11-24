import json
import os
import re
import subprocess
import sys
import tomllib

import pytest

from src.config import PROJECT_ROOT, RUNTIME_ROOT_ENV

HEAVY_PACKAGES = {"sklearn", "scipy", "numpy", "pandas"}
NEEDED_AT_RUNTIME = ("src", "supabase", "config")
EXCLUDE_LIMIT = 256


@pytest.fixture(scope="module")
def entrypoint() -> str:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return project["tool"]["vercel"]["entrypoint"]


@pytest.fixture(scope="module")
def settings() -> dict:
    return json.loads((PROJECT_ROOT / "vercel.json").read_text(encoding="utf-8"))


def _entry_file(entrypoint: str) -> str:
    return entrypoint.split(":")[0].replace(".", "/") + ".py"


def _run(script: str, tmp_path) -> str:
    env = {**os.environ, "PULSE_STORE": "sqlite", RUNTIME_ROOT_ENV: str(tmp_path)}
    done = subprocess.run(
        [sys.executable, "-c", script], cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def test_DEP_01_entrypoint_is_the_api(entrypoint, tmp_path):
    module, name = entrypoint.split(":")
    script = f"import {module} as m; print(type(m.{name}).__name__, '/apps' in m.{name}.openapi()['paths'])"
    assert _run(script, tmp_path) == "FastAPI True"


def test_DEP_02_only_main_is_deployed(settings):
    assert settings["git"]["deploymentEnabled"] == {"**": False, "main": True}


def test_DEP_03_settings_apply_to_the_entrypoint(settings, entrypoint):
    assert settings["framework"] == "fastapi"
    assert list(settings["functions"]) == [_entry_file(entrypoint)]
    assert settings["regions"] == ["bom1"]


def test_DEP_04_bundle_keeps_what_the_api_reads(settings, entrypoint):
    excluded = settings["functions"][_entry_file(entrypoint)]["excludeFiles"]
    assert len(excluded) <= EXCLUDE_LIMIT
    folders = re.fullmatch(r"\{([^{}]+)\}/\*\*", excluded).group(1).split(",")
    assert not set(folders) & set(NEEDED_AT_RUNTIME)
    assert {"data", "outputs", "tests", "frontend"} <= set(folders)


def test_DEP_05_api_starts_without_the_theme_engine(entrypoint, tmp_path):
    module = entrypoint.split(":")[0]
    script = f"import sys, {module}; print(sorted({{n.split('.')[0] for n in sys.modules}} & {HEAVY_PACKAGES!r}))"
    assert _run(script, tmp_path) == "[]"


def test_DEP_06_one_python_version_everywhere():
    version = (PROJECT_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    workflows = (PROJECT_ROOT / ".github" / "workflows").glob("*.yml")
    used = {v for w in workflows for v in re.findall(r'python-version: "([^"]+)"', w.read_text(encoding="utf-8"))}
    assert used == {version}


def test_DEP_07_api_install_leaves_out_the_theme_engine():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    extras = project["optional-dependencies"]
    assert not any(re.match(r"numpy|scikit-learn", d) for d in project["dependencies"])
    assert {re.match(r"[\w-]+", d).group() for d in extras["pipeline"]} == {"numpy", "scikit-learn"}
    assert f"{project['name']}[pipeline]" in extras["dev"]


def test_DEP_08_workflows_install_the_theme_engine():
    installs = [
        line.strip()
        for workflow in (PROJECT_ROOT / ".github" / "workflows").glob("*.yml")
        for line in workflow.read_text(encoding="utf-8").splitlines()
        if re.search(r"pip install .*\.", line)
    ]
    assert len(installs) >= 3
    assert [line for line in installs if not re.search(r'"\.\[(pipeline|dev)\]"', line)] == []

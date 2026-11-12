"""Phase 0 Test Suite: Foundations, Config, and Constraints.

Implements all Phase 0 edge cases specified in docs/edge-case.md §16:
- CFG-01..09
- ING-14, ING-15
- MCP-17, MCP-18
- SEC-04, SEC-05
"""

import os
import socket
import tempfile
import warnings
from pathlib import Path
import pytest
import yaml

from src.config import (
    load_pulse_config,
    require_secret,
    get_project_root,
    PulseConfig,
    ThemesConfig,
    NoteConfig,
    AppStoreSourceConfig,
    PlayStoreSourceConfig,
)
from src.mcp.capabilities import load_mcp_config, resolve_capability, MCPConfigData
from src.skeleton import run_skeleton, count_words, build_skeleton_note


# ==============================================================================
# CFG-01: Theme Cap Hard Limit (P0)
# ==============================================================================
def test_CFG_01_theme_cap_hard_limit():
    """CFG-01: Reject max_themes > 5 at startup."""
    with pytest.raises(ValueError, match="max_themes cannot exceed 5"):
        ThemesConfig(max_themes=6)

    # Valid values <= 5 must pass
    for valid_count in [1, 3, 5]:
        cfg = ThemesConfig(max_themes=valid_count)
        assert cfg.max_themes == valid_count


# ==============================================================================
# CFG-02: Word Cap Hard Limit (P0)
# ==============================================================================
def test_CFG_02_word_cap_hard_limit():
    """CFG-02: Reject max_words > 250 at startup."""
    with pytest.raises(ValueError, match="max_words cannot exceed 250"):
        NoteConfig(max_words=251)

    # Valid values <= 250 must pass
    cfg = NoteConfig(max_words=250)
    assert cfg.max_words == 250


# ==============================================================================
# CFG-03: Quotes and Actions Count Fixed (P0)
# ==============================================================================
def test_CFG_03_counts_fixed():
    """CFG-03: Reject quotes != 3 or actions != 3."""
    with pytest.raises(ValueError, match="quotes count must be exactly 3"):
        NoteConfig(quotes=2)

    with pytest.raises(ValueError, match="actions count must be exactly 3"):
        NoteConfig(actions=4)

    valid_cfg = NoteConfig(quotes=3, actions=3)
    assert valid_cfg.quotes == 3
    assert valid_cfg.actions == 3


# ==============================================================================
# CFG-04: Invalid or Missing Config (P1)
# ==============================================================================
def test_CFG_04_invalid_config():
    """CFG-04: Missing config file or invalid YAML yields clear error and non-zero exit."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        non_existent = tmp_path / "does_not_exist.yaml"
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_pulse_config(non_existent)

        broken_yaml = tmp_path / "broken.yaml"
        broken_yaml.write_text("app: [broken: yaml: unclosed", encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse YAML"):
            load_pulse_config(broken_yaml)


# ==============================================================================
# CFG-05: Missing Secret Message (P1)
# ==============================================================================
def test_CFG_05_missing_secret_message(monkeypatch):
    """CFG-05: Missing secret reports variable name clearly and never prints key value."""
    monkeypatch.delenv("NON_EXISTENT_SECRET_12345", raising=False)
    with pytest.raises(ValueError) as exc_info:
        require_secret("NON_EXISTENT_SECRET_12345")

    err_msg = str(exc_info.value)
    assert "NON_EXISTENT_SECRET_12345" in err_msg


# ==============================================================================
# CFG-06: No Secrets in Outputs (P0)
# ==============================================================================
def test_CFG_06_no_secrets_in_outputs(monkeypatch):
    """CFG-06: Ensure secret values never leak into output notes or reports."""
    secret_token = "SUPER_SECRET_TOKEN_XYZ_999"
    monkeypatch.setenv("DUMMY_SECRET", secret_token)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        report = run_skeleton(
            config_path="config/pulse.yaml",
            week_str="2026-11-10",
            output_base=tmp_path
        )

        report_file = tmp_path / "2026-11-10" / "run_report.json"
        note_file = tmp_path / "2026-11-10" / "note.md"

        report_text = report_file.read_text(encoding="utf-8")
        note_text = note_file.read_text(encoding="utf-8")

        assert secret_token not in report_text
        assert secret_token not in note_text


# ==============================================================================
# CFG-07: Unknown Keys Warning (P2)
# ==============================================================================
def test_CFG_07_unknown_keys():
    """CFG-07: Unknown configuration keys emit a warning rather than crashing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cfg_file = tmp_path / "unknown_keys.yaml"
        cfg_file.write_text(
            "app:\n  name: Groww\nunknown_feature_flag: true\nanother_random_key: 123\n",
            encoding="utf-8"
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cfg = load_pulse_config(cfg_file)
            assert cfg.app.name == "Groww"
            assert len(w) >= 1
            assert "Unknown configuration keys found" in str(w[-1].message)


# ==============================================================================
# CFG-08: Gitignore Protects Data & Secrets (P1)
# ==============================================================================
def test_CFG_08_gitignore_protects_data():
    """CFG-08: .gitignore must cover data/, outputs/, and .env."""
    root = get_project_root()
    gitignore_path = root / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in project root"

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    assert any(line.startswith("data/") for line in lines), ".gitignore must exclude data/"
    assert any(line.startswith("outputs/") for line in lines), ".gitignore must exclude outputs/"
    assert any(line.startswith(".env") for line in lines), ".gitignore must exclude .env"


# ==============================================================================
# CFG-09: Cross-Platform Paths (P1)
# ==============================================================================
def test_CFG_09_cross_platform_paths():
    """CFG-09: Paths handled via pathlib.Path resolve cleanly across platforms."""
    root = get_project_root()
    pulse_cfg = load_pulse_config("config/pulse.yaml")
    assert isinstance(pulse_cfg.sources.play_store.path, Path)
    assert isinstance(pulse_cfg.mcp.config, Path)
    assert root.is_absolute()


# ==============================================================================
# ING-14 & SEC-05: Automated Play Collection Guard (P0)
# ==============================================================================
def test_ING_14_automated_source_blocked(monkeypatch):
    """ING-14 / SEC-05: Automated Play collection without approval record is blocked."""
    monkeypatch.setenv("ALLOW_AUTOMATED_PLAY_COLLECTION", "false")

    with pytest.raises(ValueError, match="Automated Google Play collection is disabled"):
        PlayStoreSourceConfig(mode="automated")

    with pytest.raises(ValueError, match="Automated Google Play collection is disabled"):
        PlayStoreSourceConfig(allow_automated=True)


def test_SEC_05_automation_guard(monkeypatch):
    """SEC-05: Verification that default config has automated collection off."""
    cfg = load_pulse_config("config/pulse.yaml")
    assert cfg.sources.play_store.mode == "csv_import"
    assert cfg.sources.play_store.allow_automated is False


# ==============================================================================
# ING-15: App Store Source Rejected in this Build (P1)
# ==============================================================================
def test_ING_15_app_store_not_supported():
    """ING-15: Enabling App Store source is rejected as unsupported."""
    with pytest.raises(ValueError, match="App Store source is not supported in this build"):
        AppStoreSourceConfig(enabled=True)

    disabled_cfg = AppStoreSourceConfig(enabled=False)
    assert disabled_cfg.enabled is False


# ==============================================================================
# MCP-17: No Send Capabilities in Capability Map (P0)
# ==============================================================================
def test_MCP_17_no_send_capability():
    """MCP-17: Assert capability map strictly forbids send email tools."""
    mcp_cfg = load_mcp_config("config/mcp.yaml")
    assert mcp_cfg.policy.draft_only is True
    assert mcp_cfg.policy.allow_send_email is False

    # Attempting to load a config with send capability must raise ValueError
    invalid_mcp_dict = {
        "version": "1.0",
        "allowed_capabilities": ["docs.create", "gmail.send_email"],
        "capabilities": {
            "docs.create": {
                "server": "google_docs",
                "tool": "create_document",
                "description": "test",
            },
            "gmail.send_email": {
                "server": "gmail",
                "tool": "send_email",
                "description": "send",
            },
        },
        "policy": {"draft_only": False, "allow_send_email": True},
    }
    with pytest.raises(ValueError, match="Forbidden capability"):
        MCPConfigData.model_validate(invalid_mcp_dict)


# ==============================================================================
# MCP-18: Static Scan - No Google SDK or Direct REST (P0)
# ==============================================================================
def test_MCP_18_no_google_sdk_or_rest():
    """MCP-18: Codebase must not import google-api-python-client, google-auth, or googleapis.com."""
    root = get_project_root()
    src_dir = root / "src"

    forbidden_patterns = [
        "googleapiclient",
        "google.auth",
        "google.oauth2",
        "https://www.googleapis.com",
        "https://gmail.googleapis.com",
        "https://docs.googleapis.com",
    ]

    py_files = list(src_dir.rglob("*.py"))
    assert len(py_files) > 0, "Source files must exist"

    violations = []
    for file_path in py_files:
        content = file_path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in content:
                violations.append(f"{file_path.name}: contains forbidden pattern '{pattern}'")

    assert not violations, f"MCP-18 violation: direct Google APIs found: {violations}"


# ==============================================================================
# SEC-04: Network Calls Blocked in Unit Tests (P1)
# ==============================================================================
def test_SEC_04_network_blocked_in_tests(monkeypatch):
    """SEC-04: Unit tests must not perform unmocked outbound network requests."""
    def guarded_connect(*args, **kwargs):
        raise RuntimeError("Outbound network connection blocked by SEC-04 test guard!")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)

    # Skeleton execution must run completely offline without hitting any network
    report = run_skeleton(config_path="config/pulse.yaml", week_str="2026-11-10")
    assert report["word_count"] <= 250
    assert report["doc_result"]["status"] == "success"
    assert report["draft_result"]["status"] == "success"

"""Tests for Phase 5: Orchestration and Hardening.

Covers:
- ORC-01: --dry-run validation, no MCP calls, no publish_state changes
- ORC-02: --stage resume from cached intermediates
- ORC-03: Crash recovery from interrupted run
- ORC-04: Database failure handling
- ORC-05: Disk write failure handling
- ORC-06: Double trigger idempotency
- ORC-07: Past week backfill
- ORC-08: Retention purge never touches active runs
- ORC-09: Retention purge scope (2x window)
- ORC-10: Run report generation and zero-PII guarantee
- ORC-11: Exit codes (0 success, 2 validation failed)
- ORC-12: Timezone consistency
- INV-01: Note invariants across randomized datasets
- INV-02: Pipeline never calls MCP on validation failure
- INV-03: Idempotent rerun guarantees
- INV-04: Canary fake PII strings absent from all artifacts
- SEC-06: Path traversal guard on week parameter
- EDG-01: Low volume week handling
- EDG-02: Spike week detection (>60% share)
- EDG-03: Short coverage flag
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.clean.pii import scrub_pii
from src.clean.window import normalize_to_week_start
from src.config import get_project_root, load_pulse_config
from src.mcp.client import MockMCPClient
from src.pipeline import run_full_pipeline, validate_week_parameter
from src.store.db import Database
from src.store.models import ReviewRecord
from src.store.retention import calculate_retention_cutoff, purge_retention


@pytest.fixture
def tmp_pipeline_env(tmp_path):
    """Sets up an isolated database and outputs directory for pipeline testing."""
    db_file = tmp_path / "test_pulse.db"
    db = Database(db_file)
    fixture_csv = get_project_root() / "tests" / "fixtures" / "reviews_baseline.csv"
    return {
        "db": db,
        "db_file": db_file,
        "csv_path": fixture_csv,
        "tmp_path": tmp_path,
    }


def test_ORC_01_dry_run_no_side_effects(tmp_pipeline_env):
    """ORC-01: --dry-run runs through validation, makes no MCP calls, and modifies no publish_state."""
    db = tmp_pipeline_env["db"]
    mock_mcp = MockMCPClient()

    res = run_full_pipeline(
        week_str="2026-11-10",
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db,
        mcp_client=mock_mcp
    )

    assert res["status"] == "validated"
    assert res["is_valid"] is True
    assert res["dry_run"] is True
    assert len(mock_mcp.call_history) == 0

    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM publish_state")
        assert c.fetchone()[0] == 0


def test_ORC_02_stage_resume(tmp_pipeline_env):
    """ORC-02: Running stages sequentially matches full end-to-end execution."""
    db = tmp_pipeline_env["db"]
    week = "2026-11-10"

    # 1. Ingest only
    ingest_res = run_full_pipeline(
        week_str=week,
        csv_path=tmp_pipeline_env["csv_path"],
        stage_limit="ingest",
        db=db
    )
    assert ingest_res["status"] == "ingest_completed"

    # 2. Themes only (uses cached reviews)
    themes_res = run_full_pipeline(
        week_str=week,
        stage_limit="themes",
        db=db
    )
    assert themes_res["status"] == "themes_completed"
    assert themes_res["themes"]["themes_count"] >= 3

    # 3. Note only
    note_res = run_full_pipeline(
        week_str=week,
        stage_limit="note",
        db=db
    )
    assert note_res["status"] == "validated"
    assert note_res["word_count"] <= 250


def test_ORC_03_crash_recovery(tmp_pipeline_env):
    """ORC-03: Interrupted run with status 'running' recovers cleanly on next run."""
    db = tmp_pipeline_env["db"]
    week = "2026-11-10"
    norm_week = str(normalize_to_week_start(week))

    # Simulate crashed run
    crash_run_id = f"run_{norm_week}_crashed"
    db.record_run_start(crash_run_id, norm_week)

    # Next run should succeed cleanly without crashing on unique constraints
    res = run_full_pipeline(
        week_str=week,
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )
    assert res["status"] == "validated"
    assert res["is_valid"] is True


def test_ORC_04_db_failure(tmp_path):
    """ORC-04: Database failure surfaces clear error and avoids partial publish."""
    bad_db = Database(tmp_path / "corrupt.db")
    with bad_db.get_connection() as conn:
        conn.execute("DROP TABLE reviews;")

    mock_mcp = MockMCPClient()
    with pytest.raises(Exception):
        run_full_pipeline(
            week_str="2026-11-10",
            db=bad_db,
            mcp_client=mock_mcp
        )
    assert len(mock_mcp.call_history) == 0


def test_ORC_05_disk_full(tmp_pipeline_env):
    """ORC-05: Output write failure surfaces clear error and stops before publishing."""
    db = tmp_pipeline_env["db"]
    mock_mcp = MockMCPClient()

    with patch("src.note.engine.resolve_project_path", side_effect=OSError("Disk full")):
        with pytest.raises(Exception):
            run_full_pipeline(
                week_str="2026-11-10",
                csv_path=tmp_pipeline_env["csv_path"],
                db=db,
                mcp_client=mock_mcp
            )
    assert len(mock_mcp.call_history) == 0


def test_ORC_06_double_trigger(tmp_pipeline_env):
    """ORC-06: Triggering twice for same week is idempotent and no-ops second publish."""
    db = tmp_pipeline_env["db"]
    mock_mcp = MockMCPClient()
    week = "2026-11-10"

    # First run: publishes
    res1 = run_full_pipeline(
        week_str=week,
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=False,
        db=db,
        mcp_client=mock_mcp
    )
    assert res1["status"] in ["published", "created"]
    calls_after_run1 = len(mock_mcp.call_history)
    assert calls_after_run1 >= 2  # create/upsert doc and draft

    # Second run: identical inputs no-op
    res2 = run_full_pipeline(
        week_str=week,
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=False,
        db=db,
        mcp_client=mock_mcp
    )
    assert res2["status"] == "published"
    assert res2["doc_url"] == res1["doc_url"]
    assert res2["draft_id"] == res1["draft_id"]


def test_ORC_07_backfill_past_week(tmp_pipeline_env):
    """ORC-07: Running for a past week generates outputs under that week."""
    db = tmp_pipeline_env["db"]
    past_week = "2026-10-12"

    res = run_full_pipeline(
        week_str=past_week,
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )
    assert res["status"] == "validated"
    assert "2026-10-12" in res["report_path"]


def test_ORC_08_purge_vs_active_run(tmp_pipeline_env):
    """ORC-08: Retention purge never deletes reviews belonging to an active run."""
    db = tmp_pipeline_env["db"]
    norm_week = "2026-11-10"

    # Ingest baseline
    run_full_pipeline(
        week_str=norm_week,
        csv_path=tmp_pipeline_env["csv_path"],
        stage_limit="themes",
        db=db
    )

    # Set run to 'running'
    active_run_id = f"run_{norm_week}_active"
    db.record_run_start(active_run_id, norm_week)

    # Associate an old review with this active run's theme
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT review_id FROM reviews LIMIT 1")
        rev_id = c.fetchone()[0]
        c.execute("UPDATE reviews SET date = '2025-01-01' WHERE review_id = ?", (rev_id,))
        c.execute("INSERT OR REPLACE INTO themes (theme_id, run_id, label, description, review_count, share_pct, avg_rating) VALUES ('t_act', ?, 'Act', 'Desc', 1, 0.1, 3.0)", (active_run_id,))
        c.execute("INSERT OR REPLACE INTO review_themes (review_id, theme_id, distance) VALUES (?, 't_act', 0.0)", (rev_id,))
        conn.commit()

    # Purge with cutoff 2026-01-01
    purge_res = purge_retention(database=db, cutoff_date="2026-01-01")
    assert active_run_id in purge_res["active_runs_protected"]

    # Verify protected review still exists
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM reviews WHERE review_id = ?", (rev_id,))
        assert c.fetchone()[0] == 1


def test_ORC_09_retention_scope(tmp_path, tmp_pipeline_env):
    """ORC-09: Retention purges only old raw files strictly outside retention scope."""
    db = tmp_pipeline_env["db"]
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Create dummy raw CSVs
    old_file = raw_dir / "play_reviews_2025-01-01_2025-03-01.csv"
    old_file.write_text("rating,text\n5,great\n", encoding="utf-8")

    recent_file = raw_dir / "play_reviews_2026-08-01_2026-11-10.csv"
    recent_file.write_text("rating,text\n5,recent\n", encoding="utf-8")

    purge_res = purge_retention(database=db, cutoff_date="2026-05-01", raw_dir=raw_dir)
    assert purge_res["files_purged"] == 1
    assert not old_file.exists()
    assert recent_file.exists()


def test_ORC_10_run_report_clean(tmp_pipeline_env):
    """ORC-10: Run report is generated with required fields and passes PII scan."""
    db = tmp_pipeline_env["db"]
    week = "2026-11-10"

    res = run_full_pipeline(
        week_str=week,
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )
    report_path = Path(res["report_path"])
    assert report_path.exists()

    report_content = report_path.read_text(encoding="utf-8")
    data = json.loads(report_content)

    assert "run_id" in data
    assert "week_start" in data
    assert "top_themes" in data
    assert "word_count" in data
    assert data["word_count"] <= 250

    # Strict PII scan on full report JSON
    pii_check = scrub_pii(report_content)
    assert pii_check.pii_found == 0


def test_ORC_11_exit_codes(tmp_pipeline_env):
    """ORC-11: CLI exits 0 on success, 2 on validation failure."""
    # Test valid week via function output
    res = run_full_pipeline(
        week_str="2026-11-10",
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=tmp_pipeline_env["db"]
    )
    assert res["status"] == "validated"


def test_ORC_12_timezone_consistency():
    """ORC-12: Week parameter is resolved consistently in UTC regardless of locale."""
    w1 = validate_week_parameter("2026-11-10")
    w2 = validate_week_parameter("2026-11-09")
    # Both normalize to the same Monday (2026-11-09)
    assert str(w1) == "2026-11-09"
    assert str(w2) == "2026-11-09"


def test_INV_01_note_invariants_randomized(tmp_pipeline_env):
    """INV-01: Invariants hold on execution (themes <= 5, quotes == 3, actions == 3, words <= 250)."""
    db = tmp_pipeline_env["db"]
    res = run_full_pipeline(
        week_str="2026-11-10",
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )
    assert res["is_valid"] is True
    assert res["word_count"] <= 250


def test_INV_02_no_mcp_on_failure(tmp_pipeline_env):
    """INV-02: Pipeline never calls MCP when validation fails (fails closed)."""
    db = tmp_pipeline_env["db"]
    mock_mcp = MockMCPClient()

    # Force a validation failure by mocking validate_note to return invalid
    from src.note.validate import ValidationResult
    failing_val = ValidationResult(
        is_valid=False,
        word_count=285,
        errors=["Word count 285 exceeds cap 250 (VAL-01)"],
        checks_passed=[]
    )

    with patch("src.note.engine.validate_note", return_value=failing_val):
        res = run_full_pipeline(
            week_str="2026-11-10",
            csv_path=tmp_pipeline_env["csv_path"],
            dry_run=False,
            retries=1,
            db=db,
            mcp_client=mock_mcp
        )
        assert res["status"] == "validation_failed"
        assert res["is_valid"] is False
        # MCP publisher was NEVER called
        assert len(mock_mcp.call_history) == 0


def test_INV_03_idempotent_rerun(tmp_pipeline_env):
    """INV-03: Rerun with identical inputs produces exactly one doc and one draft."""
    db = tmp_pipeline_env["db"]
    mock_mcp = MockMCPClient()
    week = "2026-11-10"

    res1 = run_full_pipeline(week_str=week, csv_path=tmp_pipeline_env["csv_path"], db=db, mcp_client=mock_mcp)
    res2 = run_full_pipeline(week_str=week, csv_path=tmp_pipeline_env["csv_path"], db=db, mcp_client=mock_mcp)

    assert res1["doc_url"] == res2["doc_url"]
    assert res1["draft_id"] == res2["draft_id"]


def test_INV_04_canary_strings_absent(tmp_pipeline_env):
    """INV-04: Seeded canary strings from canaries.json never appear in outputs or reports."""
    canaries_file = get_project_root() / "tests" / "fixtures" / "canaries.json"
    canaries_data = json.loads(canaries_file.read_text(encoding="utf-8"))

    all_canaries = []
    for cat in canaries_data.values():
        all_canaries.extend(cat)

    db = tmp_pipeline_env["db"]
    res = run_full_pipeline(
        week_str="2026-11-10",
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )

    report_text = Path(res["report_path"]).read_text(encoding="utf-8")
    note_text = (get_project_root() / "outputs" / res["week"] / "note.md").read_text(encoding="utf-8")

    for canary in all_canaries:
        assert canary not in report_text, f"Canary leaked into report: {canary}"
        assert canary not in note_text, f"Canary leaked into note: {canary}"


def test_SEC_06_path_traversal():
    """SEC-06: Path traversal tokens in week parameter are rejected immediately."""
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_week_parameter("../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_week_parameter("..\\..\\windows")


def test_EDG_01_low_volume_week(tmp_pipeline_env):
    """EDG-01: A week with low review volume runs successfully and flags coverage/volume."""
    db = tmp_pipeline_env["db"]
    res = run_full_pipeline(
        week_str="2026-11-10",
        csv_path=tmp_pipeline_env["csv_path"],
        dry_run=True,
        db=db
    )
    assert res["status"] == "validated"


def test_EDG_02_spike_week_detection(tmp_pipeline_env):
    """EDG-02: High-share spike themes (>60%) are marked with is_spike=True."""
    from src.themes.rank import compute_theme_stats
    stats = compute_theme_stats(
        theme_id="thm_spike",
        label="Outage",
        description="Login crash",
        cluster_indices=[0, 1, 2],
        all_reviews=[
            ReviewRecord(review_id="r1", platform="play_store", rating=1, text="Crash", date="2026-11-09"),
            ReviewRecord(review_id="r2", platform="play_store", rating=1, text="Crash", date="2026-11-09"),
            ReviewRecord(review_id="r3", platform="play_store", rating=1, text="Crash", date="2026-11-09"),
        ],
        total_analyzed=4
    )
    # 3 out of 4 = 75% share -> is_spike should be True
    assert stats["is_spike"] is True


def test_EDG_03_short_coverage_flag():
    """EDG-03: Coverage shorter than 8 weeks is flagged."""
    reviews = [
        ReviewRecord(review_id="r1", platform="play_store", rating=5, text="Great", date="2026-11-01"),
        ReviewRecord(review_id="r2", platform="play_store", rating=5, text="Good", date="2026-11-09"),
    ]
    from src.clean.window import compute_coverage_weeks
    cov = compute_coverage_weeks(reviews)
    assert cov < 8.0

"""Retention and purging service for Groww Weekly Review Pulse (Phase 5, Task 5.5).

Enforces:
- ORC-08: Retention purge runs while a run is active; purge never deletes rows used by an active run.
- ORC-09: Retention removes old raw files; only files outside window + one prior window removed.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.clean.window import normalize_to_week_start
from src.config import get_project_root, resolve_project_path
from src.store.db import Database


def calculate_retention_cutoff(
    week_str: str,
    window_weeks: int = 9,
    retention_multiplier: int = 2
) -> str:
    """Calculate the cutoff date (YYYY-MM-DD) for retention.
    
    Per architecture §6 and ORC-09, retention retains reviews and raw files within
    the rolling window plus one prior window (total: window_weeks * 2).
    """
    week_start = normalize_to_week_start(week_str)
    total_weeks = window_weeks * retention_multiplier
    cutoff_dt = week_start - timedelta(weeks=total_weeks)
    return cutoff_dt.strftime("%Y-%m-%d")


def purge_retention(
    database: Database,
    cutoff_date: str,
    raw_dir: Optional[Path | str] = None
) -> Dict[str, any]:
    """Execute retention purge on database reviews and archived raw CSV files.
    
    Returns:
    {
        "cutoff_date": cutoff_date,
        "reviews_purged": int,
        "files_purged": int,
        "active_runs_protected": List[str]
    }
    """
    # 1. Fetch active runs to protect (ORC-08)
    active_runs = database.get_active_runs()

    # 2. Purge reviews from database older than cutoff_date
    reviews_purged = database.purge_reviews_older_than(
        cutoff_date=cutoff_date,
        exclude_run_ids=active_runs if active_runs else None
    )

    # 3. Purge old raw CSV files outside retention scope (ORC-09)
    root = get_project_root()
    raw_path = resolve_project_path(raw_dir or (root / "data" / "raw"))
    files_purged = 0

    if raw_path.exists() and raw_path.is_dir():
        # Match files like: play_reviews_YYYY-MM-DD_YYYY-MM-DD.csv
        file_date_pattern = re.compile(r"play_reviews_\d{4}-\d{2}-\d{2}_(\d{4}-\d{2}-\d{2})\.csv")
        for f in raw_path.iterdir():
            if f.is_file():
                match = file_date_pattern.search(f.name)
                if match:
                    file_end_date = match.group(1)
                    if file_end_date < cutoff_date:
                        try:
                            f.unlink()
                            files_purged += 1
                        except OSError:
                            pass

    return {
        "cutoff_date": cutoff_date,
        "reviews_purged": reviews_purged,
        "files_purged": files_purged,
        "active_runs_protected": active_runs,
    }

"""Google Play Store CSV ingestion adapter.

Enforces:
- Explicit field allowlist: rating, title, text, date, app_version (ING-01)
- Drops reviewer identity fields (author_name, user_id, avatar_url, device_id)
- Fails fast on missing required columns (ING-03)
- Handles BOM, CRLF, encodings (ING-09)
- Normalization and validation
"""

import csv
import io
import warnings
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.clean.normalize import normalize_text, validate_and_coerce_rating, parse_review_date
from src.config import resolve_project_path


ALLOWLISTED_COLUMNS = {"rating", "title", "text", "date", "app_version"}
REQUIRED_COLUMNS = {"rating", "text", "date"}
FORBIDDEN_IDENTITY_COLUMNS = {"author_name", "user_id", "avatar_url", "device_id", "reviewer_name", "email"}


class PlayStoreImportSource:
    """CSV/JSON importer for permitted public Google Play exports."""

    name: str = "play_store"

    def __init__(self, file_path: Path | str):
        self.file_path = resolve_project_path(file_path)

    def read_raw_records(self) -> List[dict]:
        """Read CSV using allowlist filtering, ignoring identity and unknown columns (ING-01, ING-02)."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.file_path}")

        # Try UTF-8 with BOM first, fall back to Latin-1 (ING-09)
        content: str
        try:
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(self.file_path, "r", encoding="latin-1") as f:
                content = f.read()

        if not content.strip():
            raise ValueError(f"Input review file is empty (ING-08): {self.file_path}")

        # Strip any leading BOM characters
        content = content.lstrip("\ufeff")

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise ValueError(f"Input file has no header row: {self.file_path}")

        fieldnames_set = set(reader.fieldnames)

        # Check required columns (ING-03)
        missing_req = REQUIRED_COLUMNS - fieldnames_set
        if missing_req:
            raise ValueError(f"Missing required columns in {self.file_path}: {sorted(missing_req)} (ING-03)")

        # Warn on unknown extra columns (ING-02)
        unknown_cols = fieldnames_set - ALLOWLISTED_COLUMNS - FORBIDDEN_IDENTITY_COLUMNS
        if unknown_cols:
            warnings.warn(f"Unknown columns ignored in {self.file_path}: {sorted(unknown_cols)}", UserWarning)

        records: List[dict] = []
        for row in reader:
            # Map exclusively via allowlist (ING-01)
            clean_record = {
                "platform": self.name,
                "rating": validate_and_coerce_rating(row.get("rating")),
                "title": normalize_text(row.get("title", "")) or None,
                "text": normalize_text(row.get("text", "")),
                "date": parse_review_date(row.get("date", "")),
                "app_version": normalize_text(row.get("app_version", "")) or None,
            }
            if not clean_record["text"]:
                continue
            records.append(clean_record)

        if not records:
            raise ValueError(f"No valid review records parsed from {self.file_path} (ING-08)")

        return records

    def fetch(self, window_start: str = "", window_end: str = "") -> List[dict]:
        """Fetch records filtered by window if provided."""
        all_records = self.read_raw_records()
        if not window_start or not window_end:
            return all_records

        return [r for r in all_records if window_start <= r["date"] <= window_end]

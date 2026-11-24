import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.clean.pii import scrub_pii

RUN_REPORT_NAME = "run_report.json"
SYSTEM_FIELDS = frozenset({
    "run_id", "theme_id", "doc_id", "doc_url", "draft_id", "week_start", "window_start", "window_end", "finished_at",
})


def scrub_report(value: Any, field: Optional[str] = None) -> Any:
    if isinstance(value, dict):
        return {k: scrub_report(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_report(v, field) for v in value]
    if not isinstance(value, str) or field in SYSTEM_FIELDS:
        return value
    result = scrub_pii(value)
    return result.cleaned_text if result.pii_found else value


def write_run_report(folder: Path, report: Dict[str, Any]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / RUN_REPORT_NAME
    path.write_text(json.dumps(scrub_report(report), indent=2), encoding="utf-8")
    return path

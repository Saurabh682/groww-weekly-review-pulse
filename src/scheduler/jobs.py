from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Mapping, Optional

from src.config import PulseConfig, load_pulse_config
from src.ingest.collect import CollectionReport, collect_app
from src.ingest.sources import ReviewSource
from src.mcp.composio import ToolCaller
from src.pipeline import run_full_pipeline
from src.scheduler.plan import JOB_MODES
from src.store.store import AppStore

GREEN_STATUSES = ("ok", "published", "low_volume", "stopped_archived")


class JobRefused(Exception):
    pass


@dataclass
class JobReport:
    app_key: str
    mode: str
    status: str
    week_start: Optional[str] = None
    collection: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.status in GREEN_STATUSES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_key": self.app_key,
            "mode": self.mode,
            "status": self.status,
            "week_start": self.week_start,
            "collection": self.collection,
        }


def latest_complete_week(today: date) -> date:
    return today - timedelta(days=today.weekday() + 7)


def _collection_summary(report: CollectionReport) -> List[Dict[str, Any]]:
    return [
        {
            "platform": r.platform,
            "status": r.status,
            "fetched": r.fetched,
            "inserted": r.inserted,
            "source_limit_hit": bool(r.source_limit_hit),
        }
        for r in report.runs
    ]


def _run_pulse(
    store: AppStore, today: date, config: PulseConfig, mcp_client: Optional[ToolCaller]
) -> tuple[str, str]:
    week_start = latest_complete_week(today).isoformat()
    result = run_full_pipeline(store=store, week_str=week_start, config=config, mcp_client=mcp_client)
    return str(result["status"]), week_start


def run_job(
    store: AppStore,
    mode: str,
    today: date,
    config: Optional[PulseConfig] = None,
    sources: Optional[Mapping[str, ReviewSource]] = None,
    mcp_client: Optional[ToolCaller] = None,
) -> JobReport:
    if mode not in JOB_MODES:
        raise JobRefused(f"Unknown mode {mode!r}. Use one of {JOB_MODES}.")
    config = config or load_pulse_config()
    app = store.refresh()
    if app.status == "archived":
        return JobReport(app.app_key, mode, "stopped_archived")
    if mode == "pulse":
        if app.status != "active":
            raise JobRefused(f"App {app.app_key!r} is {app.status}; a pulse needs an active app.")
        status, week_start = _run_pulse(store, today, config, mcp_client)
        return JobReport(app.app_key, mode, status, week_start)

    collected = collect_app(store, mode, today, config, sources)
    summary = _collection_summary(collected)
    if collected.app_status == "archived":
        return JobReport(app.app_key, mode, "stopped_archived", collection=summary)
    if collected.failed:
        return JobReport(app.app_key, mode, "failed", collection=summary)
    if mode != "backfill":
        return JobReport(app.app_key, mode, "ok", collection=summary)
    status, week_start = _run_pulse(store, today, config, mcp_client)
    return JobReport(app.app_key, mode, status, week_start, summary)

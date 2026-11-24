from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from src.store.models import AppRecord

DAILY_CRON = "30 20 * * *"
PULSE_CRON = "30 3 * * 1"
RECONCILE_CRON = "30 21 1 * *"
CRON_MODES: Dict[str, str] = {DAILY_CRON: "daily", PULSE_CRON: "pulse", RECONCILE_CRON: "reconcile"}
JOB_MODES = ("backfill", "daily", "pulse", "reconcile")
SCHEDULE_EVENT = "schedule"
DISPATCH_EVENT = "workflow_dispatch"

MODE_BY_STATUS: Dict[str, Dict[str, str]] = {
    "backfill": {status: "backfill" for status in ("pending_backfill", "backfilling", "active", "failed")},
    "daily": {"active": "daily", "pending_backfill": "backfill", "backfilling": "backfill"},
    "pulse": {"active": "pulse"},
    "reconcile": {"active": "reconcile"},
}


class PlanError(Exception):
    pass


@dataclass(frozen=True)
class Job:
    app_key: str
    mode: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def resolve_request(event: str, schedule: str, mode: str, app_key: str) -> Tuple[str, Optional[str]]:
    if event == SCHEDULE_EVENT:
        if schedule not in CRON_MODES:
            raise PlanError(f"Unknown cron {schedule!r}. Known crons: {sorted(CRON_MODES)}.")
        return CRON_MODES[schedule], None
    if event != DISPATCH_EVENT:
        raise PlanError(f"Unsupported event {event!r}. Use {SCHEDULE_EVENT} or {DISPATCH_EVENT}.")
    if mode not in JOB_MODES:
        raise PlanError(f"Unknown mode {mode!r}. Use one of {JOB_MODES}.")
    selected = app_key.strip()
    if mode == "backfill" and not selected:
        raise PlanError("mode=backfill needs app_key. Name one registered app.")
    return mode, selected or None


def plan_jobs(mode: str, app_key: Optional[str], apps: Sequence[AppRecord]) -> List[Job]:
    modes = MODE_BY_STATUS[mode]
    if app_key is None:
        return [Job(a.app_key, modes[a.status]) for a in sorted(apps, key=lambda a: a.app_key) if a.status in modes]
    app = next((a for a in apps if a.app_key == app_key), None)
    if app is None:
        raise PlanError(f"No app registered with app_key {app_key!r}.")
    if app.status not in modes:
        raise PlanError(f"App {app_key!r} is {app.status}; mode={mode} accepts {sorted(modes)}.")
    return [Job(app.app_key, modes[app.status])]

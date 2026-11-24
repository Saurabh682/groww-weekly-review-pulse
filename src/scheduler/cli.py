import argparse
import json
import os
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, List, Optional

from src.config import PROJECT_ROOT, load_pulse_config
from src.ingest.collect import CollectionRefused
from src.mcp.errors import MCPMissingSetting
from src.scheduler.jobs import JobRefused, run_job
from src.scheduler.logscan import LogScanner
from src.scheduler.plan import JOB_MODES, PlanError, plan_jobs, resolve_request
from src.store.errors import UnknownApp
from src.store.factory import open_store

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REFUSED = 2
EXIT_LOG_WITHHELD = 3
PRINTABLE_ERRORS = (PlanError, JobRefused, CollectionRefused, MCPMissingSetting, UnknownApp)
REVIEW_MARGIN_WEEKS = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.scheduler", description="Scheduled collection and pulse jobs")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Resolve this run's jobs and write them to GITHUB_OUTPUT")
    run = sub.add_parser("run", help="Run one job for one app")
    show = sub.add_parser("show-log", help="Print a captured job log only when the scan finds nothing private")
    for command in (run, show):
        command.add_argument("--app", required=True, help="Registered app_key")
    run.add_argument("--mode", required=True, choices=JOB_MODES)
    show.add_argument("--file", required=True, type=Path)
    return parser


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _plan() -> int:
    mode, app_key = resolve_request(
        os.getenv("GITHUB_EVENT_NAME", ""),
        os.getenv("PULSE_SCHEDULE", ""),
        os.getenv("PULSE_MODE", ""),
        os.getenv("PULSE_APP_KEY", ""),
    )
    jobs = json.dumps([j.to_dict() for j in plan_jobs(mode, app_key, open_store().list_apps())])
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"jobs={jobs}\n")
    print(json.dumps({"mode": mode, "jobs": json.loads(jobs)}))
    return EXIT_OK


def _run(app_key: str, mode: str) -> int:
    report = run_job(open_store().for_app(app_key), mode, utc_today())
    print(json.dumps(report.to_dict(), indent=2))
    if not report.succeeded:
        print("Details are in the collection_runs and runs tables.")
    return EXIT_OK if report.succeeded else EXIT_FAILED


def _stored_review_texts(app_key: str) -> Iterator[str]:
    today = utc_today()
    start = today - timedelta(weeks=load_pulse_config().window.weeks + REVIEW_MARGIN_WEEKS)
    for review in open_store().for_app(app_key).get_reviews_in_window(start.isoformat(), today.isoformat()):
        yield review.text
        yield review.title or ""


def _show_log(app_key: str, path: Path) -> int:
    log_text = path.read_text(encoding="utf-8", errors="replace")
    findings = LogScanner(log_text).findings(_stored_review_texts(app_key))
    if findings:
        print(f"error: job log withheld, it contains: {', '.join(findings)}", file=sys.stderr)
        return EXIT_LOG_WITHHELD
    print(log_text)
    return EXIT_OK


def project_location(exc: BaseException) -> str:
    frames = traceback.extract_tb(exc.__traceback__)
    own = [f for f in frames if Path(f.filename).is_relative_to(PROJECT_ROOT / "src")]
    last = (own or frames)[-1]
    return f"{Path(last.filename).name}:{last.lineno}"


def run(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            return _plan()
        if args.command == "run":
            return _run(args.app, args.mode)
        return _show_log(args.app, args.file)
    except PRINTABLE_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except Exception as exc:
        print(f"error: {type(exc).__name__} at {project_location(exc)}", file=sys.stderr)
        return EXIT_FAILED

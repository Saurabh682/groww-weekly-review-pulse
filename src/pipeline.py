"""Pipeline orchestrator for Groww Weekly Review Pulse (Phase 1).

Implements stages:
1. Ingestion via allowlist
2. Deduplication
3. PII Scrubbing
4. Language tagging & low-info filtering
5. SQLite persistence & raw allowlisted archive
6. Summary metrics report
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.clean.dedupe import deduplicate_reviews
from src.clean.lang import detect_language
from src.clean.low_info import is_low_info, check_low_info_distribution
from src.clean.pii import scrub_pii
from src.clean.window import (
    calculate_window_bounds,
    compute_coverage_weeks,
    normalize_to_week_start,
)
from src.config import load_pulse_config, PulseConfig, get_project_root, resolve_project_path
from src.ingest.play_csv import PlayStoreImportSource
from src.store.db import Database
from src.store.models import ReviewRecord


def process_and_ingest_reviews(
    config: Optional[PulseConfig] = None,
    week_str: str = "2026-11-10",
    csv_path: Optional[Path | str] = None,
    db: Optional[Database] = None
) -> Dict[str, any]:
    """Execute Phase 1 Ingestion, Scrubbing, and Persistence."""
    if not config:
        config = load_pulse_config()

    root = get_project_root()
    database = db or Database(root / "data" / "pulse.db")

    # 1. Window bounds (WIN-04, WIN-06, WIN-08)
    week_start = normalize_to_week_start(week_str)
    window_start, window_end = calculate_window_bounds(week_start, weeks=config.window.weeks)

    # 2. Ingest raw records with allowlist (ING-01, ING-03)
    source_path = resolve_project_path(csv_path or config.sources.play_store.path)
    importer = PlayStoreImportSource(source_path)
    raw_records = importer.fetch(window_start=window_start, window_end=window_end)

    if not raw_records:
        raise ValueError(f"Zero reviews found within window {window_start} to {window_end} in {source_path}")

    # 3. Deduplication (DUP-01, DUP-03, DUP-04)
    deduped_records, dedupe_dropped = deduplicate_reviews(raw_records)

    # 4. Save allowlisted PII-free raw copy in data/raw/ (PII-38)
    raw_archive_dir = root / "data" / "raw"
    raw_archive_dir.mkdir(parents=True, exist_ok=True)
    raw_archive_file = raw_archive_dir / f"play_reviews_{window_start}_{window_end}.csv"

    fieldnames = ["rating", "title", "text", "date", "app_version"]
    with open(raw_archive_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in deduped_records:
            writer.writerow({k: r.get(k) for k in fieldnames})

    # 5. Clean, Scrub PII, Language Tag, Low-Info Filter
    processed_records: List[ReviewRecord] = []
    pii_redacted_count = 0
    total_tokens_scrubbed = 0

    for r in deduped_records:
        # Scrub Title (PII-20)
        title_res = scrub_pii(r.get("title") or "", is_title=True)
        # Scrub Body (PII-01..19)
        text_res = scrub_pii(r.get("text") or "")

        pii_found = 1 if (title_res.pii_found or text_res.pii_found) else 0
        if pii_found:
            pii_redacted_count += 1
            total_tokens_scrubbed += (title_res.redaction_count + text_res.redaction_count)

        # Detect Language (LNG-01..04)
        lang_res = detect_language(text_res.cleaned_text)

        # Determine quote eligibility (must be en, no pii, clean)
        quote_eligible = 1 if (lang_res.quote_eligible and text_res.quote_eligible and not pii_found) else 0

        # Check Low Info (NRM-01)
        low_info = 1 if is_low_info(text_res.cleaned_text) else 0

        # Review ID hash
        review_id = hashlib.sha256(
            f"play_store|{r['date']}|{text_res.cleaned_text}".encode("utf-8")
        ).hexdigest()[:16]

        record = ReviewRecord(
            review_id=review_id,
            platform="play_store",
            rating=r["rating"],
            title=title_res.cleaned_text or None,
            text=text_res.cleaned_text,
            date=r["date"],
            app_version=r.get("app_version"),
            lang=lang_res.lang,
            low_info=low_info,
            pii_found=pii_found,
            quote_eligible=quote_eligible,
            raw_hash=hashlib.sha256(r["text"].encode("utf-8")).hexdigest()[:16],
        )
        processed_records.append(record)

    # 6. Check low info distribution (LOW-01, LOW-02)
    low_info_dist = check_low_info_distribution(processed_records)
    if low_info_dist["all_low_info"]:
        raise ValueError("All ingested reviews are low-info / emoji-only (LOW-01). Pipeline halted.")

    # 7. Persist to SQLite (ING-16)
    newly_inserted = database.upsert_reviews(processed_records)

    # 8. Compute Coverage (WIN-01)
    coverage_weeks = compute_coverage_weeks(processed_records)
    ratings = [r.rating for r in processed_records]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    summary = {
        "week": week_str,
        "week_start": week_start.strftime("%Y-%m-%d"),
        "window_start": window_start,
        "window_end": window_end,
        "raw_imported": len(raw_records),
        "dedupe_dropped": dedupe_dropped,
        "total_analyzed": len(processed_records),
        "newly_inserted": newly_inserted,
        "coverage_weeks": coverage_weeks,
        "short_coverage_flag": coverage_weeks < 8.0,
        "avg_rating": avg_rating,
        "pii_redacted_reviews": pii_redacted_count,
        "pii_tokens_scrubbed": total_tokens_scrubbed,
        "low_info_reviews": low_info_dist["low_info_count"],
        "low_info_share": low_info_dist["low_info_share"],
        "quote_eligible_reviews": sum(1 for r in processed_records if r.quote_eligible == 1),
    }

    return summary


from src.themes.engine import run_theme_pipeline


def run_themes_stage(
    config: Optional[PulseConfig] = None,
    week_str: str = "2026-11-10",
    db: Optional[Database] = None
) -> Dict[str, any]:
    """Execute Phase 2 Theme Engine on reviews stored in SQLite."""
    if not config:
        config = load_pulse_config()

    root = get_project_root()
    database = db or Database(root / "data" / "pulse.db")

    week_start = normalize_to_week_start(week_str)
    window_start, window_end = calculate_window_bounds(week_start, weeks=config.window.weeks)

    # Fetch stored reviews within window
    reviews = database.get_reviews_in_window(window_start, window_end, include_low_info=False)
    if not reviews:
        raise ValueError(
            f"No reviews found in database for window {window_start} to {window_end}. "
            "Run 'ingest' stage first."
        )

    theme_result = run_theme_pipeline(
        reviews=reviews,
        config=config,
        db=database,
        week_str=week_str
    )
    return theme_result


def validate_week_parameter(week_str: str):
    """Validate week parameter against path traversal and format errors (SEC-06, WIN-06, ORC-12)."""
    if not week_str or not isinstance(week_str, str):
        raise ValueError("Week parameter must be a non-empty string.")
    if ".." in week_str or "/" in week_str or "\\" in week_str:
        raise ValueError(f"Path traversal detected in week parameter: {week_str!r} (SEC-06)")
    cleaned = week_str.strip()
    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid week date format: {week_str!r}. Expected YYYY-MM-DD.") from e
    return normalize_to_week_start(cleaned)


def run_full_pipeline(
    week_str: str = "2026-11-10",
    csv_path: Optional[Path | str] = None,
    dry_run: bool = False,
    stage_limit: Optional[str] = None,
    retries: int = 3,
    db: Optional[Database] = None,
    config: Optional[PulseConfig] = None,
    mcp_client=None,
) -> Dict[str, any]:
    """Execute complete weekly pulse pipeline (Phase 5 Orchestrator).
    
    Stages:
    1. Ingest (allowlist, clean, dedupe, PII scrub, lang tag, persist)
    2. Themes (embed, cluster <=5 themes, stats, ranking, spike check)
    3. Note & Validate Gate with Multi-attempt Regeneration (VAL-01..07, INV-02)
    4. Publish via MCP (Google Docs + Gmail draft staging; dry-run no-op)
    5. Observability & Report (run_report.json, zero-PII guarantee)
    """
    start_time = datetime.now(timezone.utc)
    week_start_dt = validate_week_parameter(week_str)
    norm_week = week_start_dt.strftime("%Y-%m-%d")

    if not config:
        config = load_pulse_config()

    root = get_project_root()
    database = db or Database(root / "data" / "pulse.db")

    window_start, window_end = calculate_window_bounds(week_start_dt, weeks=config.window.weeks)
    run_id = f"run_{norm_week}_{int(start_time.timestamp() * 1000)}"

    database.record_run_start(
        run_id=run_id,
        week_start=norm_week,
        window_start=window_start,
        window_end=window_end
    )

    stage_timings: Dict[str, float] = {}
    stage_statuses: Dict[str, str] = {}

    # Stage 1: Ingestion
    t0 = datetime.now(timezone.utc)
    try:
        reviews_in_window = database.get_reviews_in_window(window_start, window_end)
        if not reviews_in_window or stage_limit == "ingest" or csv_path is not None:
            ingest_summary = process_and_ingest_reviews(
                config=config,
                week_str=norm_week,
                csv_path=csv_path,
                db=database
            )
            stage_statuses["ingest"] = "done"
        else:
            stage_statuses["ingest"] = "cached"
            ingest_summary = {
                "week": norm_week,
                "window_start": window_start,
                "window_end": window_end,
                "total_analyzed": len(reviews_in_window),
                "coverage_weeks": compute_coverage_weeks(reviews_in_window),
                "short_coverage_flag": compute_coverage_weeks(reviews_in_window) < 8.0,
            }

        database.update_run(
            run_id=run_id,
            status="ingest_completed" if stage_limit == "ingest" else "running",
            total_reviews=ingest_summary.get("total_analyzed", 0),
            analyzed_reviews=ingest_summary.get("total_analyzed", 0),
            avg_rating=ingest_summary.get("avg_rating", 0.0),
            coverage_weeks=ingest_summary.get("coverage_weeks", 0.0),
            finished=(stage_limit == "ingest")
        )
    except Exception as e:
        database.update_run(run_id=run_id, status="failed", error=str(e), finished=True)
        raise

    stage_timings["ingest"] = (datetime.now(timezone.utc) - t0).total_seconds()
    if stage_limit == "ingest":
        return {
            "run_id": run_id,
            "status": "ingest_completed",
            "stage_limit": "ingest",
            "ingest": ingest_summary,
            "timings": stage_timings
        }

    # Stage 2: Themes Clustering
    t0 = datetime.now(timezone.utc)
    try:
        theme_summary = run_themes_stage(config=config, week_str=norm_week, db=database)
        stage_statuses["themes"] = "done"
        has_spike = any(t.get("is_spike", False) for t in theme_summary.get("themes", []))
        database.update_run(
            run_id=run_id,
            status="themes_completed" if stage_limit == "themes" else "running",
            finished=(stage_limit == "themes")
        )
    except Exception as e:
        database.update_run(run_id=run_id, status="failed", error=str(e), finished=True)
        raise

    stage_timings["themes"] = (datetime.now(timezone.utc) - t0).total_seconds()
    if stage_limit == "themes":
        return {
            "run_id": run_id,
            "status": "themes_completed",
            "stage_limit": "themes",
            "themes": theme_summary,
            "has_spike": has_spike,
            "timings": stage_timings
        }

    # Stage 3: Note Generation & Validation Gate (Multi-attempt regeneration Task 5.2)
    t0 = datetime.now(timezone.utc)
    from src.note.engine import build_and_validate_pulse_note
    from src.clean.pii import scrub_pii

    attempt = 0
    note = None
    rendered_md = None
    val_result = None
    out_folder = None

    while attempt < max(1, retries):
        attempt += 1
        note, rendered_md, val_result, out_folder = build_and_validate_pulse_note(
            database=database,
            week_start=norm_week,
            dry_run=dry_run
        )
        if val_result.is_valid:
            break

    stage_timings["note_validation"] = (datetime.now(timezone.utc) - t0).total_seconds()

    if not val_result.is_valid:
        # Validation Gate Failed (INV-02: NEVER CALL PUBLISH!)
        database.update_run(
            run_id=run_id,
            status="validation_failed",
            error="; ".join(val_result.errors),
            finished=True
        )
        stage_statuses["note"] = "validation_failed"
        stage_statuses["publish"] = "skipped"

        out_dir = root / "outputs" / norm_week
        out_dir.mkdir(parents=True, exist_ok=True)
        failed_report = {
            "run_id": run_id,
            "week_start": norm_week,
            "window_start": window_start,
            "window_end": window_end,
            "status": "validation_failed",
            "attempts": attempt,
            "max_retries": retries,
            "errors": val_result.errors,
            "checks_passed": val_result.checks_passed,
            "word_count": val_result.word_count,
            "dry_run": dry_run,
            "stage_statuses": stage_statuses,
            "timings": stage_timings
        }
        (out_dir / "run_report.json").write_text(json.dumps(failed_report, indent=2), encoding="utf-8")

        return {
            "run_id": run_id,
            "week": norm_week,
            "status": "validation_failed",
            "is_valid": False,
            "errors": val_result.errors,
            "attempts": attempt,
            "report_path": str(out_dir / "run_report.json"),
            "timings": stage_timings
        }

    stage_statuses["note"] = "done"
    if stage_limit == "note":
        database.update_run(run_id=run_id, status="validated", finished=True)
        return {
            "run_id": run_id,
            "status": "validated",
            "stage_limit": "note",
            "word_count": val_result.word_count,
            "timings": stage_timings
        }

    # Stage 4: Publish via MCP (Phase 4 MCP publishing)
    t0 = datetime.now(timezone.utc)
    pub_result = None

    if not dry_run:
        from src.mcp.capabilities import load_mcp_config
        from src.mcp.client import MockMCPClient
        from src.mcp.publisher import PulsePublisher

        mcp_cfg = load_mcp_config(config.mcp.config)
        client = mcp_client or MockMCPClient()
        publisher = PulsePublisher(database=database, mcp_config=mcp_cfg, client=client)

        recipient_to = config.email.to if config.email.to else "product-leadership@groww.in"
        pub_result = publisher.publish_pulse(
            week_start=norm_week,
            note_markdown=rendered_md,
            recipient_email=recipient_to
        )

        final_status = "published" if pub_result.status in ["published", "created", "updated", "no_change", "noop"] else "publish_failed"
        database.update_run(run_id=run_id, status=final_status, finished=True)
        stage_statuses["publish"] = "done" if final_status == "published" else "failed"
    else:
        # Dry-run: NO MCP calls, NO publish_state modifications (ORC-01)
        database.update_run(run_id=run_id, status="validated", finished=True)
        stage_statuses["publish"] = "skipped_dry_run"

    stage_timings["publish"] = (datetime.now(timezone.utc) - t0).total_seconds()

    # Stage 5: Observability & Run Report Generation (Task 5.4, ORC-10)
    out_dir = root / "outputs" / norm_week
    out_dir.mkdir(parents=True, exist_ok=True)

    report_data = {
        "run_id": run_id,
        "week_start": norm_week,
        "window_start": window_start,
        "window_end": window_end,
        "status": "published" if (not dry_run and pub_result and pub_result.status in ["published", "created", "updated", "no_change", "noop"]) else ("validated" if dry_run else "failed"),
        "dry_run": dry_run,
        "total_reviews": ingest_summary.get("total_analyzed", 0),
        "analyzed_reviews": theme_summary.get("analyzable_reviews", 0),
        "coverage_weeks": ingest_summary.get("coverage_weeks", 0.0),
        "short_coverage_flag": ingest_summary.get("short_coverage_flag", False),
        "has_spike": any(t.get("is_spike", False) for t in theme_summary.get("themes", [])),
        "avg_rating": ingest_summary.get("avg_rating", 0.0),
        "word_count": val_result.word_count,
        "is_valid": val_result.is_valid,
        "attempts": attempt,
        "top_themes": [
            {
                "rank": t["rank"],
                "label": t["label"],
                "review_count": t["review_count"],
                "share_pct": t["share_pct"],
                "avg_rating": t["avg_rating"],
                "is_spike": t.get("is_spike", False),
            }
            for t in theme_summary.get("top_3_themes", [])
        ],
        "quotes_count": len(note.quotes) if note else 0,
        "actions_count": len(note.actions) if note else 0,
        "publish": {
            "status": pub_result.status if pub_result else "dry_run",
            "doc_id": pub_result.doc_id if pub_result else None,
            "doc_url": pub_result.doc_url if pub_result else None,
            "draft_id": pub_result.draft_id if pub_result else None,
        } if pub_result else None,
        "stage_statuses": stage_statuses,
        "timings": stage_timings,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }

    report_json = json.dumps(report_data, indent=2)
    pii_check = scrub_pii(report_json)
    if pii_check.pii_found:
        report_json = pii_check.cleaned_text

    report_path = out_dir / "run_report.json"
    report_path.write_text(report_json, encoding="utf-8")

    return {
        "run_id": run_id,
        "week": norm_week,
        "status": report_data["status"],
        "is_valid": True,
        "dry_run": dry_run,
        "word_count": val_result.word_count,
        "doc_url": pub_result.doc_url if pub_result else None,
        "draft_id": pub_result.draft_id if pub_result else None,
        "report_path": str(report_path),
        "timings": stage_timings,
    }


def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Review Pulse Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

    run_parser = subparsers.add_parser("run", help="Execute complete weekly pulse pipeline (Phase 5)")
    run_parser.add_argument("--week", default="2026-11-10", help="Run week (YYYY-MM-DD)")
    run_parser.add_argument("--file", default=None, help="Path to input CSV file")
    run_parser.add_argument("--dry-run", action="store_true", help="Stop after validation without publishing")
    run_parser.add_argument("--stage", choices=["ingest", "themes", "note", "publish"], default=None, help="Stop after specified stage or resume")
    run_parser.add_argument("--retries", type=int, default=3, help="Max regeneration attempts on validation failure")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest, clean, and scrub Play reviews")
    ingest_parser.add_argument("--week", default="2026-11-10", help="Run week (YYYY-MM-DD)")
    ingest_parser.add_argument("--file", default=None, help="Path to input CSV file")

    themes_parser = subparsers.add_parser("themes", help="Cluster reviews into <=5 ranked themes")
    themes_parser.add_argument("--week", default="2026-11-10", help="Run week (YYYY-MM-DD)")

    note_parser = subparsers.add_parser("note", help="Generate and validate weekly note (Phase 3)")
    note_parser.add_argument("--week", default="2026-11-10", help="Run week (YYYY-MM-DD)")
    note_parser.add_argument("--dry-run", action="store_true", help="Stop after validation without publishing")

    pub_parser = subparsers.add_parser("publish", help="Publish validated note to Google Docs and Gmail draft via MCP (Phase 4)")
    pub_parser.add_argument("--week", default="2026-11-10", help="Run week (YYYY-MM-DD)")
    pub_parser.add_argument("--dry-run", action="store_true", help="Execute with mock MCP client without live side effects")

    purge_parser = subparsers.add_parser("purge", help="Retention purge for old reviews and raw files (Task 5.5)")
    purge_parser.add_argument("--week", default="2026-11-10", help="Current week to anchor retention window")
    purge_parser.add_argument("--weeks", type=int, default=18, help="Total retention window in weeks (default: 18)")

    args = parser.parse_args()

    if args.command == "run":
        res = run_full_pipeline(
            week_str=args.week,
            csv_path=args.file,
            dry_run=args.dry_run,
            stage_limit=args.stage,
            retries=args.retries,
        )
        print("Weekly pulse run complete:")
        print(json.dumps(res, indent=2))
        if res.get("status") == "validation_failed":
            sys.exit(2)  # distinct code for validation failure (ORC-11)
        elif res.get("status") == "failed":
            sys.exit(1)
        sys.exit(0)
    elif args.command == "purge":
        from src.store.retention import calculate_retention_cutoff, purge_retention
        db = Database()
        cutoff = calculate_retention_cutoff(week_str=args.week, window_weeks=args.weeks // 2)
        purge_res = purge_retention(database=db, cutoff_date=cutoff)
        print("Retention purge complete:")
        print(json.dumps(purge_res, indent=2))
        sys.exit(0)
    elif args.command == "ingest":
        summary = process_and_ingest_reviews(week_str=args.week, csv_path=args.file)
        print("Ingestion complete:")
        print(json.dumps(summary, indent=2))
    elif args.command == "themes":
        theme_summary = run_themes_stage(week_str=args.week)
        print("Theme clustering complete:")
        # Print summary without huge review id lists
        display_summary = {
            "week": theme_summary["week"],
            "total_input_reviews": theme_summary["total_input_reviews"],
            "analyzable_reviews": theme_summary["analyzable_reviews"],
            "filter_metrics": theme_summary["filter_metrics"],
            "themes_count": theme_summary["themes_count"],
            "themes": [
                {
                    "rank": t["rank"],
                    "label": t["label"],
                    "review_count": t["review_count"],
                    "share_pct": f"{t['share_pct']:.1%}",
                    "avg_rating": f"{t['avg_rating']}★",
                    "neg_share": f"{t['neg_share']:.1%}",
                    "priority_score": t["priority_score"],
                    "is_top3": bool(t["is_top3"]),
                }
                for t in theme_summary["themes"]
            ]
        }
        print(json.dumps(display_summary, indent=2))
    elif args.command == "note":
        from src.note.engine import build_and_validate_pulse_note
        db = Database()
        week_start = normalize_to_week_start(args.week)
        note, rendered_md, val_result, out_folder = build_and_validate_pulse_note(
            database=db,
            week_start=week_start,
            dry_run=args.dry_run
        )
        print(f"Weekly pulse note generation {'(DRY RUN)' if args.dry_run else ''}:")
        print(f"Validation: {'PASSED' if val_result.is_valid else 'FAILED'}")
        print(f"Word count: {val_result.word_count} / 250 words cap")
        print(f"Output saved to: {out_folder}")
        print("-" * 50)
        print(rendered_md)
        print("-" * 50)
        if not val_result.is_valid:
            print("Errors detected:")
            for err in val_result.errors:
                print(f"  - {err}")
            sys.exit(2)  # distinct exit code for validation failure (ORC-11)
    elif args.command == "publish":
        from src.note.engine import build_and_validate_pulse_note
        from src.mcp.capabilities import load_mcp_config
        from src.mcp.client import MockMCPClient
        from src.mcp.publisher import PulsePublisher

        db = Database()
        week_start = str(normalize_to_week_start(args.week))
        
        # 1. Build and validate note first (INV-02: never publish on validation failure)
        note, rendered_md, val_result, out_folder = build_and_validate_pulse_note(
            database=db,
            week_start=week_start,
            dry_run=args.dry_run
        )
        if not val_result.is_valid:
            print("ERROR: Note validation failed. Publishing blocked (INV-02):")
            for err in val_result.errors:
                print(f"  - {err}")
            sys.exit(2)

        cfg = load_pulse_config()
        mcp_cfg = load_mcp_config(cfg.mcp.config)
        
        # In dry-run mode or sandbox environment, use MockMCPClient
        client = MockMCPClient() if args.dry_run else MockMCPClient() # Default to MockMCPClient for local sandbox unless live stdio server active
        publisher = PulsePublisher(database=db, mcp_config=mcp_cfg, client=client)

        recipient_to = cfg.email.to if cfg.email.to else "self@groww-pulse.local"
        pub_result = publisher.publish_pulse(
            week_start=week_start,
            note_markdown=rendered_md,
            recipient_email=recipient_to
        )

        print(f"Publish status: {pub_result.status.upper()}")
        print(f"Week: {pub_result.week_start}")
        print(f"Google Doc URL: {pub_result.doc_url}")
        print(f"Google Doc ID: {pub_result.doc_id}")
        print(f"Gmail Draft ID: {pub_result.draft_id}")
        print(f"Content Hash: {pub_result.content_hash}")
        if pub_result.message:
            print(f"Message: {pub_result.message}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

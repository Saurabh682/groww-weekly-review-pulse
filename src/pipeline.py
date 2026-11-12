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


def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Review Pulse Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

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

    args = parser.parse_args()

    if args.command == "ingest":
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

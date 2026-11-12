"""Full note generation and validation workflow for Groww Weekly Review Pulse (Phase 3)."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import resolve_project_path
from src.note.generate import enforce_word_budget, synthesize_action_items, synthesize_theme_one_liner
from src.note.models import ThemeSummary, WeeklyPulseNote
from src.note.render import render_html, render_markdown, render_plain_text
from src.note.select import select_quotes_for_themes
from src.note.validate import ValidationResult, validate_note
from src.note.words import count_note_words
from src.store.db import Database
from src.store.models import ReviewRecord, RunRecord, ThemeRecord


def build_and_validate_pulse_note(
    database: Database,
    week_start: str | date,
    output_dir: Optional[Path | str] = None,
    dry_run: bool = False
) -> Tuple[WeeklyPulseNote, str, ValidationResult, Path]:
    """Build, render, and validate a weekly pulse note for the specified week.
    
    Returns:
    (note_object, rendered_markdown, validation_result, output_folder)
    """
    week_start = str(week_start)
    # 1. Fetch run record
    with database.get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM runs 
            WHERE week_start = ? OR week_start LIKE ? OR run_id LIKE ?
            ORDER BY created_at DESC LIMIT 1
        """, (week_start, f"{week_start[:7]}%", f"%{week_start}%"))
        row = c.fetchone()
        if not row:
            # Fallback to latest run if any
            c.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 1")
            row = c.fetchone()
        if not row:
            raise ValueError(f"No run record found in database for week {week_start}. Run 'pulse themes' first.")
        run_record = RunRecord(**dict(row))

        # 2. Fetch themes for this run
        c.execute("SELECT * FROM themes WHERE run_id = ? ORDER BY is_top3 DESC, share_pct DESC", (run_record.run_id,))
        themes = [ThemeRecord(**dict(r)) for r in c.fetchall()]
        if not themes:
            raise ValueError(f"No themes found for run {run_record.run_id}.")

        top_themes = [t for t in themes if t.is_top3]
        if not top_themes:
            top_themes = themes[:3]

        # 3. Fetch reviews assigned to themes
        c.execute("""
            SELECT r.*, rt.theme_id
            FROM reviews r
            JOIN review_themes rt ON r.review_id = rt.review_id
            JOIN themes t ON rt.theme_id = t.theme_id
            WHERE t.run_id = ?
        """, (run_record.run_id,))
        
        theme_reviews: Dict[str, List[ReviewRecord]] = {}
        all_assigned_reviews: Dict[str, ReviewRecord] = {}
        for r in c.fetchall():
            d = dict(r)
            tid = d.pop("theme_id")
            rev = ReviewRecord(**d)
            all_assigned_reviews[rev.review_id] = rev
            theme_reviews.setdefault(tid, []).append(rev)

    # 4. Extract verbatim quotes
    selected_quotes = select_quotes_for_themes(
        top_themes=top_themes,
        theme_reviews=theme_reviews,
        max_quotes=3
    )

    # 5. Synthesize theme summaries with one-liners
    theme_summaries: List[ThemeSummary] = []
    for t in top_themes:
        one_liner = synthesize_theme_one_liner(t)
        theme_summaries.append(ThemeSummary(
            theme_id=t.theme_id,
            label=t.label,
            description=t.description,
            one_liner=one_liner,
            review_count=t.review_count,
            share_pct=t.share_pct,
            avg_rating=t.avg_rating,
            neg_share=t.neg_share,
            is_top3=True
        ))

    # 6. Synthesize grounded action items
    action_items = synthesize_action_items(top_themes)

    # Compute window dates from week_start
    # Note covers week_start backwards ~9 weeks
    from datetime import datetime, timedelta
    dt_end = datetime.strptime(week_start, "%Y-%m-%d")
    dt_start = dt_end - timedelta(weeks=run_record.coverage_weeks if run_record.coverage_weeks > 0 else 8.0)
    window_start_str = dt_start.strftime("%Y-%m-%d")

    # 7. Construct WeeklyPulseNote
    note = WeeklyPulseNote(
        week_start=week_start,
        window_start=window_start_str,
        window_end=week_start,
        platform="Google Play",
        total_reviews=run_record.total_reviews,
        analyzed_reviews=run_record.analyzed_reviews,
        avg_rating=run_record.avg_rating,
        top_themes=theme_summaries,
        quotes=selected_quotes,
        actions=action_items,
        coverage_weeks=run_record.coverage_weeks,
        short_coverage_flag=run_record.coverage_weeks < 8.0
    )

    # 8. Render and enforce word budget
    rendered_md = render_markdown(note)
    rendered_md = enforce_word_budget(rendered_md, max_words=250)

    # 9. Validate note against hard invariants
    validation = validate_note(
        note=note,
        rendered_text=rendered_md,
        source_reviews=all_assigned_reviews
    )

    # 10. Write local artifacts
    if output_dir:
        out_folder = resolve_project_path(output_dir)
    else:
        out_folder = resolve_project_path(f"outputs/{week_start}")
        from src.config import get_project_root
        out_folder = get_project_root() / f"outputs/{week_start}"
    out_folder.mkdir(parents=True, exist_ok=True)

    note_path = out_folder / "note.md"
    note_path.write_text(rendered_md, encoding="utf-8")

    # Write HTML and text variants
    (out_folder / "note.html").write_text(render_html(note), encoding="utf-8")
    (out_folder / "note.txt").write_text(render_plain_text(note), encoding="utf-8")

    # Write run report
    report = {
        "run_id": run_record.run_id,
        "week_start": week_start,
        "status": "validated" if validation.is_valid else "validation_failed",
        "word_count": validation.word_count,
        "max_words_allowed": 250,
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "checks_passed": validation.checks_passed,
        "top_themes": [t.to_dict() for t in theme_summaries],
        "quotes_count": len(selected_quotes),
        "actions_count": len(action_items),
        "dry_run": dry_run
    }
    (out_folder / "run_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    return note, rendered_md, validation, out_folder

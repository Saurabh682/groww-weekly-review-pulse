"""Full note generation and validation workflow for weekly review pulse notes (Phase 3)."""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.clean.window import is_short_coverage
from src.config import outputs_root, resolve_project_path
from src.domains import domain_pack_for
from src.note.coverage import build_store_coverage
from src.note.generate import enforce_word_budget, synthesize_action_items, synthesize_theme_one_liner
from src.note.models import ThemeSummary, WeeklyPulseNote
from src.note.render import render_html, render_markdown, render_plain_text
from src.note.select import select_quotes_for_themes
from src.note.validate import ValidationResult, validate_note
from src.run_report import write_run_report
from src.store.models import ReviewRecord
from src.store.store import AppStore


def build_and_validate_pulse_note(
    store: AppStore,
    week_start: str | date,
    output_dir: Optional[Path | str] = None,
    dry_run: bool = False
) -> Tuple[WeeklyPulseNote, str, ValidationResult, Path]:
    """Build, render, and validate a weekly pulse note for the specified week.

    Returns:
    (note_object, rendered_markdown, validation_result, output_folder)
    """
    week_start = str(week_start)
    run_record = store.latest_themed_run_for_week(week_start)
    if run_record is None:
        raise ValueError(
            f"No themed run found for app {store.app_key!r} and week {week_start}. Run 'pulse themes' first."
        )

    if run_record.window_start is None or run_record.window_end is None:
        raise ValueError(
            f"Run {run_record.run_id} has no stored review window. Run the 'themes' stage again for week {week_start}."
        )

    themes = store.get_themes(run_record.run_id)
    if not themes:
        raise ValueError(f"No themes found for run {run_record.run_id}.")

    top_themes = [t for t in themes if t.is_top3]
    if not top_themes:
        top_themes = themes[:3]

    theme_reviews: Dict[str, List[ReviewRecord]] = store.get_theme_reviews(run_record.run_id)
    all_assigned_reviews: Dict[str, ReviewRecord] = {
        rev.review_id: rev for revs in theme_reviews.values() for rev in revs
    }
    pack = domain_pack_for(store.app.category)

    # 4. Extract verbatim quotes
    selected_quotes = select_quotes_for_themes(
        top_themes=top_themes,
        theme_reviews=theme_reviews,
        max_quotes=3
    )

    # 5. Synthesize theme summaries with one-liners
    theme_summaries: List[ThemeSummary] = []
    for t in top_themes:
        one_liner = synthesize_theme_one_liner(t, pack)
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
    action_items = synthesize_action_items(top_themes, pack)

    # 7. Construct WeeklyPulseNote
    note = WeeklyPulseNote(
        week_start=week_start,
        window_start=run_record.window_start,
        window_end=run_record.window_end,
        app_name=store.app.display_name,
        store_coverage=build_store_coverage(store, run_record.window_start, run_record.window_end),
        total_reviews=run_record.total_reviews,
        analyzed_reviews=run_record.analyzed_reviews,
        avg_rating=run_record.avg_rating,
        top_themes=theme_summaries,
        quotes=selected_quotes,
        actions=action_items,
        coverage_weeks=run_record.coverage_weeks,
        short_coverage_flag=is_short_coverage(run_record.coverage_weeks)
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
        out_folder = outputs_root() / store.app_key / week_start
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
    write_run_report(out_folder, report)

    return note, rendered_md, validation, out_folder

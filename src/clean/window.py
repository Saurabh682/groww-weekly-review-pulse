"""Time window calculations and coverage validation (WIN-01..08)."""

from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple
from src.store.models import ReviewRecord


def normalize_to_week_start(input_date_str: str, reference_date: date = None) -> date:
    """Normalize input date to Monday-start ISO week date (WIN-06).
    Rejects future week dates (WIN-08).
    """
    try:
        parsed = datetime.strptime(input_date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid week date format '{input_date_str}'. Expected YYYY-MM-DD.") from exc

    today = reference_date or datetime.now(timezone.utc).date()
    # Normalize to Monday of that week
    monday = parsed - timedelta(days=parsed.weekday())

    # Check future week
    current_monday = today - timedelta(days=today.weekday())
    if monday > current_monday:
        raise ValueError(f"Week date '{input_date_str}' ({monday}) is in the future (WIN-08).")

    return monday


def calculate_window_bounds(week_start: date, weeks: int = 12) -> Tuple[str, str]:
    """Calculate [window_start, window_end] inclusive in YYYY-MM-DD format (WIN-04).
    
    Window ends on Sunday of the target week, and starts 'weeks' prior on Monday.
    Enforces weeks between 8 and 12 (WIN-03).
    """
    if weeks < 8 or weeks > 12:
        raise ValueError(f"Window weeks must be between 8 and 12 (WIN-03, got {weeks}).")

    sunday_end = week_start + timedelta(days=6)
    monday_start = week_start - timedelta(weeks=weeks - 1)

    return monday_start.strftime("%Y-%m-%d"), sunday_end.strftime("%Y-%m-%d")


def compute_coverage_weeks(reviews: List[ReviewRecord]) -> float:
    """Calculate actual weeks spanned by reviews (WIN-01)."""
    if not reviews:
        return 0.0

    dates = [datetime.strptime(r.date, "%Y-%m-%d").date() for r in reviews]
    min_date = min(dates)
    max_date = max(dates)
    days_span = (max_date - min_date).days + 1
    return round(days_span / 7.0, 1)

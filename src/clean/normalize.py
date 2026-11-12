"""Review text normalization, date parsing, and rating validation.

Handles:
- Unicode NFKC normalization and control character stripping (NRM-02)
- Rating coercion and validation 1-5 (ING-05)
- Date parsing to UTC YYYY-MM-DD and future date rejection (ING-06, ING-07)
- Missing title handling (ING-04)
"""

import re
import unicodedata
from datetime import datetime, date, timezone
from typing import Optional, Tuple


ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F\u00A0]")
WHITESPACE_PATTERN = re.compile(r"\s+")
EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u27ff\u2b50\u2b55\u231a\u231b\u23f0-\u23f3\u25aa\u25ab\u25fe\u25fd]",
    flags=re.UNICODE,
)


def remove_emojis(text: Optional[str]) -> str:
    """Remove emojis from text."""
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", str(text))
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def normalize_text(text: Optional[str]) -> str:
    """Normalize text: NFKC, straight quotes, whitespace collapse, strip zero-width characters."""
    if not text:
        return ""
    # NFKC
    nfkc = unicodedata.normalize("NFKC", str(text))
    # Remove zero-width / invisible chars
    cleaned = ZERO_WIDTH_PATTERN.sub(" ", nfkc)
    # Convert curly quotes to straight
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Collapse whitespace runs
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def validate_and_coerce_rating(raw_rating: any) -> int:
    """Validate rating is integer 1-5. Coerces 4.0 -> 4. Rejects out of range or non-numeric (ING-05)."""
    if raw_rating is None:
        raise ValueError("Rating cannot be None")

    if isinstance(raw_rating, (int, float)):
        val = int(raw_rating)
        if val != raw_rating and not (isinstance(raw_rating, float) and raw_rating.is_integer()):
            raise ValueError(f"Rating cannot be a fractional float: {raw_rating}")
        if 1 <= val <= 5:
            return val
        raise ValueError(f"Rating out of range 1-5: {val}")

    if isinstance(raw_rating, str):
        cleaned = raw_rating.strip()
        try:
            float_val = float(cleaned)
            if float_val.is_integer():
                val = int(float_val)
                if 1 <= val <= 5:
                    return val
            raise ValueError(f"Invalid rating value: {raw_rating}")
        except ValueError as exc:
            raise ValueError(f"Non-numeric rating: {raw_rating}") from exc

    raise ValueError(f"Unsupported rating type: {type(raw_rating)}")


def parse_review_date(raw_date: any, reference_date: Optional[date] = None) -> str:
    """Parse various date formats into UTC YYYY-MM-DD. Rejects future dates (ING-06, ING-07)."""
    if not raw_date:
        raise ValueError("Date cannot be empty")

    today = reference_date or datetime.now(timezone.utc).date()
    parsed_date: Optional[date] = None

    if isinstance(raw_date, (datetime, date)):
        parsed_date = raw_date if isinstance(raw_date, date) else raw_date.date()
    elif isinstance(raw_date, str):
        cleaned = raw_date.strip()
        # Try standard formats: ISO (YYYY-MM-DD), DD/MM/YYYY, MM/DD/YYYY
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                parsed_date = dt.date()
                break
            except ValueError:
                continue

    if not parsed_date:
        raise ValueError(f"Unrecognized date format: {raw_date}")

    # Check future date (ING-07) with 1 day clock-skew tolerance
    if parsed_date > today:
        delta = (parsed_date - today).days
        if delta > 1:
            raise ValueError(f"Future date rejected (ING-07): {parsed_date} > {today}")

    return parsed_date.strftime("%Y-%m-%d")

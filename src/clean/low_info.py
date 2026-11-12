"""Low-information and emoji-only review detection (NRM-01, LOW-01, LOW-02)."""

import re
from typing import List
from src.store.models import ReviewRecord


def is_low_info(text: str, min_tokens: int = 3) -> bool:
    """Identify empty, emoji-only, or very short generic reviews.
    
    Tokens are alphanumeric words of length >= 2.
    Reviews with fewer than min_tokens or only emojis/punctuation are low-info (NRM-01).
    """
    if not text:
        return True

    # Find words with at least one alphanumeric character
    tokens = [t for t in re.findall(r"\b\w+\b", text) if len(t) >= 1]
    return len(tokens) < min_tokens


def check_low_info_distribution(reviews: List[ReviewRecord]) -> dict:
    """Analyze the proportion of low-info reviews in a dataset (LOW-01, LOW-02)."""
    if not reviews:
        return {
            "total": 0,
            "low_info_count": 0,
            "low_info_share": 1.0,
            "all_low_info": True,
            "mostly_low_info": True,
        }

    total = len(reviews)
    low_info_count = sum(1 for r in reviews if r.low_info == 1)
    share = low_info_count / total

    return {
        "total": total,
        "low_info_count": low_info_count,
        "low_info_share": round(share, 3),
        "all_low_info": low_info_count == total,
        "mostly_low_info": share >= 0.85,
    }

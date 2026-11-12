"""Filtering rules for Phase 2 theme analysis.

User constraints applied:
1. Reviews with more than 8 words are kept.
2. Emojis are removed from review text.
3. English reviews only (Hindi, Hinglish, and other languages removed).
"""

import re
from typing import List, Tuple
from src.clean.normalize import remove_emojis
from src.store.models import ReviewRecord


def count_words(text: str) -> int:
    """Count words in text using whitespace/word boundaries."""
    return len(re.findall(r"\b\w+\b", text))


def prepare_reviews_for_themes(
    reviews: List[ReviewRecord],
    min_word_count: int = 8,
    required_lang: str = "en"
) -> Tuple[List[ReviewRecord], dict]:
    """Filter and clean reviews according to Phase 2 user specifications:
    - lang == required_lang ('en')
    - Emojis stripped
    - Words > min_word_count (default 8)
    
    Returns (filtered_reviews, filter_metrics).
    """
    filtered: List[ReviewRecord] = []
    dropped_lang = 0
    dropped_short = 0
    emojis_stripped_count = 0

    for r in reviews:
        # 1. English filter
        if r.lang != required_lang:
            dropped_lang += 1
            continue

        # 2. Strip emojis
        clean_text = remove_emojis(r.text)
        if clean_text != r.text:
            emojis_stripped_count += 1

        # 3. Word count filter: reviews which are more than 8 words
        words = count_words(clean_text)
        if words <= min_word_count:
            dropped_short += 1
            continue

        # Create updated record
        updated_record = ReviewRecord(
            review_id=r.review_id,
            platform=r.platform,
            rating=r.rating,
            title=remove_emojis(r.title) if r.title else None,
            text=clean_text,
            date=r.date,
            app_version=r.app_version,
            lang=r.lang,
            low_info=0,
            pii_found=r.pii_found,
            quote_eligible=r.quote_eligible,
            raw_hash=r.raw_hash,
            created_at=r.created_at,
        )
        filtered.append(updated_record)

    metrics = {
        "initial_count": len(reviews),
        "kept_count": len(filtered),
        "dropped_non_english": dropped_lang,
        "dropped_short_reviews": dropped_short,
        "emojis_stripped_count": emojis_stripped_count,
    }

    return filtered, metrics

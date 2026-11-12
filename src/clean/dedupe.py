"""Deduplication and near-duplicate collapse (DUP-01..05)."""

import hashlib
import re
from typing import Dict, List, Set, Tuple


def compute_exact_hash(platform: str, date_str: str, text: str) -> str:
    """Exact dedupe hash: sha256(platform | date | normalized_text) (DUP-01)."""
    raw = f"{platform}|{date_str}|{text.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_token_shingles(text: str, k: int = 2) -> Set[str]:
    """Generate k-shingles of words for Jaccard similarity."""
    tokens = [t.lower() for t in re.findall(r"\b\w+\b", text)]
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_similarity(s1: Set[str], s2: Set[str]) -> float:
    """Compute Jaccard similarity between two shingle sets."""
    if not s1 or not s2:
        return 0.0
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    return intersection / union if union > 0 else 0.0


def deduplicate_reviews(
    reviews: List[dict],
    similarity_threshold: float = 0.85,
    allow_short_generic_duplicates: bool = True
) -> Tuple[List[dict], int]:
    """Deduplicate reviews using exact matching and near-duplicate shingling.
    
    Protects short generic genuine reviews from over-collapse (DUP-04).
    Returns (deduplicated_reviews, count_dropped).
    """
    seen_exact_hashes: Set[str] = set()
    unique_reviews: List[dict] = []
    dropped_count = 0

    # Short generic phrases that shouldn't be collapsed if on different dates or by different users
    generic_short_phrases = {
        "good app", "nice app", "best app", "superb", "very good",
        "awesome", "bad app", "worst app", "great app"
    }

    # Cluster index for near-duplicate check per date
    date_shingles: Dict[str, List[Tuple[Set[str], str]]] = {}

    for rev in reviews:
        platform = rev.get("platform", "play_store")
        date_str = rev.get("date", "")
        text = rev.get("text", "")
        clean_text = text.strip().lower()

        exact_hash = compute_exact_hash(platform, date_str, clean_text)
        if exact_hash in seen_exact_hashes:
            dropped_count += 1
            continue

        # Check if text is short generic
        tokens = clean_text.split()
        is_short_generic = clean_text in generic_short_phrases or len(tokens) <= 2

        if allow_short_generic_duplicates and is_short_generic:
            # Keep short generic duplicates across instances
            seen_exact_hashes.add(exact_hash)
            unique_reviews.append(rev)
            continue

        # Near-duplicate check against reviews on the same date (DUP-03, DUP-05)
        shingles = compute_token_shingles(clean_text)
        is_near_dup = False

        if date_str in date_shingles:
            for existing_shingles, existing_text in date_shingles[date_str]:
                sim = jaccard_similarity(shingles, existing_shingles)
                if sim >= similarity_threshold:
                    is_near_dup = True
                    break

        if is_near_dup:
            dropped_count += 1
            continue

        seen_exact_hashes.add(exact_hash)
        if date_str not in date_shingles:
            date_shingles[date_str] = []
        date_shingles[date_str].append((shingles, clean_text))
        unique_reviews.append(rev)

    return unique_reviews, dropped_count

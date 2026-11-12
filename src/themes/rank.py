"""Theme statistics, priority ranking, and top 3 selection (THM-12..18)."""

from typing import Dict, List, Optional
import numpy as np
from src.store.models import ReviewRecord


def compute_theme_stats(
    theme_id: str,
    label: str,
    description: str,
    cluster_indices: List[int],
    all_reviews: List[ReviewRecord],
    total_analyzed: int,
    prior_theme_stats: Optional[Dict[str, dict]] = None
) -> dict:
    """Compute metrics for a single theme cluster."""
    cluster_reviews = [all_reviews[i] for i in cluster_indices]
    count = len(cluster_reviews)
    share_pct = round(count / total_analyzed, 4) if total_analyzed > 0 else 0.0

    ratings = [r.rating for r in cluster_reviews]
    # Handle uniform ratings and division by zero (THM-12)
    avg_rating = round(float(np.mean(ratings)), 2) if ratings else 0.0

    # Negative ratings (ratings <= 2)
    neg_count = sum(1 for r in cluster_reviews if r.rating <= 2)
    # neg_share extreme handling 0 or 1 without NaN (THM-14)
    neg_share = round(neg_count / count, 4) if count > 0 else 0.0

    # Priority score formula per architecture §7.3:
    # priority_score = share_pct * (0.6 + 0.4 * neg_share)
    priority_score = round(share_pct * (0.6 + 0.4 * neg_share), 5)

    # Week-over-week trend (THM-18)
    growth = 0.0
    trend = "n/a"
    if prior_theme_stats and label in prior_theme_stats:
        prior_share = prior_theme_stats[label].get("share_pct", 0.0)
        growth = round(share_pct - prior_share, 4)
        trend = f"{growth:+.1%}"

    # Outage week spike detection (>60% share) (THM-17)
    is_spike = share_pct > 0.60

    return {
        "theme_id": theme_id,
        "label": label,
        "description": description,
        "review_count": count,
        "share_pct": share_pct,
        "avg_rating": avg_rating,
        "neg_share": neg_share,
        "priority_score": priority_score,
        "growth": growth,
        "trend": trend,
        "is_spike": is_spike,
        "is_top3": 0,
        "member_review_ids": [r.review_id for r in cluster_reviews],
    }


def rank_themes(
    themes: List[dict],
    enforce_issue_in_top3: bool = True
) -> List[dict]:
    """Rank themes by priority_score with deterministic tie-breaking (THM-13) and positive dominance guard (THM-15).
    
    Tie-break order:
    1. priority_score (desc)
    2. neg_share (desc)
    3. growth (desc)
    4. label (asc)
    """
    if not themes:
        return []

    # Sort with deterministic tie-break (THM-13)
    sorted_themes = sorted(
        themes,
        key=lambda t: (
            -t["priority_score"],
            -t["neg_share"],
            -t["growth"],
            t["label"].lower(),
        )
    )

    # Positive Dominance Policy (THM-15):
    # If all top 3 are positive (avg_rating >= 4.0 or neg_share < 0.2), and an issue-oriented
    # theme exists in the remaining themes with min share, promote it into position 3.
    if enforce_issue_in_top3 and len(sorted_themes) >= 3:
        top3 = sorted_themes[:3]
        all_top_positive = all(t["avg_rating"] >= 4.0 or t["neg_share"] < 0.15 for t in top3)

        if all_top_positive:
            # Look for an issue-oriented theme outside top 3
            for i in range(3, len(sorted_themes)):
                candidate = sorted_themes[i]
                if candidate["neg_share"] >= 0.30 or candidate["avg_rating"] <= 3.0:
                    # Swap into 3rd position
                    sorted_themes[2], sorted_themes[i] = sorted_themes[i], sorted_themes[2]
                    break

    # Mark top 3
    for i, t in enumerate(sorted_themes):
        t["rank"] = i + 1
        t["is_top3"] = 1 if i < 3 else 0

    return sorted_themes

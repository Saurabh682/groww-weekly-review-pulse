"""Phase 2 Theme Engine coordinator."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import PulseConfig, get_project_root, load_pulse_config
from src.store.db import Database
from src.store.models import ReviewRecord
from src.themes.cluster import cluster_reviews
from src.themes.embed import Embedder
from src.themes.filter import prepare_reviews_for_themes
from src.themes.label import label_cluster
from src.themes.rank import compute_theme_stats, rank_themes


def run_theme_pipeline(
    reviews: List[ReviewRecord],
    config: Optional[PulseConfig] = None,
    db: Optional[Database] = None,
    week_str: str = "2026-11-10",
    run_id: Optional[str] = None
) -> Dict[str, any]:
    """Execute Phase 2 Theme Engine on a dataset of reviews."""
    if not config:
        config = load_pulse_config()

    root = get_project_root()
    database = db or Database(root / "data" / "pulse.db")
    active_run_id = run_id or f"run_{week_str}_{int(hashlib.md5(week_str.encode()).hexdigest(), 16) % 100000}"

    # 1. Apply User Phase 2 Filters:
    # - More than 8 words
    # - Strip emojis
    # - English reviews only
    filtered_reviews, filter_metrics = prepare_reviews_for_themes(
        reviews,
        min_word_count=8,
        required_lang="en"
    )

    if len(filtered_reviews) < 2:
        raise ValueError(
            f"Fewer than 2 analyzable reviews after filtering ({len(filtered_reviews)} remaining). "
            "Cannot form pulse themes (THM-03)."
        )

    # 2. Vector Embedding (with SQLite cache THM-10, THM-11)
    embedder = Embedder(db=database, model_name=f"{config.llm.provider}-lsa-64")
    vectors = embedder.embed_reviews(filtered_reviews)

    # 3. Capped Clustering (THM-01..09)
    clusters, centroids, cluster_meta = cluster_reviews(
        vectors=vectors,
        reviews=filtered_reviews,
        min_k=config.themes.top_n,
        max_k=config.themes.max_themes,
        min_cluster_share=config.themes.min_cluster_share,
        random_state=42
    )

    # 4. Labeling & Statistics
    used_labels = set()
    raw_themes: List[dict] = []

    for cluster_idx, member_indices in clusters.items():
        cluster_texts = [filtered_reviews[i].text for i in member_indices]
        cluster_ratings = [filtered_reviews[i].rating for i in member_indices]
        avg_rating = sum(cluster_ratings) / len(cluster_ratings)
        centroid = centroids[cluster_idx]

        theme_id = f"thm_{week_str}_{cluster_idx + 1}"
        label, description = label_cluster(
            cluster_texts=cluster_texts,
            cluster_centroid=centroid,
            avg_rating=avg_rating,
            used_labels=used_labels
        )

        stats = compute_theme_stats(
            theme_id=theme_id,
            label=label,
            description=description,
            cluster_indices=member_indices,
            all_reviews=filtered_reviews,
            total_analyzed=len(filtered_reviews)
        )
        raw_themes.append(stats)

    # 5. Priority Ranking & Top 3 Selection (THM-13, THM-15)
    ranked_themes = rank_themes(raw_themes, enforce_issue_in_top3=True)

    # 6. Persist Run and Themes to SQLite
    now_iso = datetime.now(timezone.utc).isoformat()
    ratings = [r.rating for r in filtered_reviews]
    overall_avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    with database.get_connection() as conn:
        cursor = conn.cursor()
        # Record in runs table first for foreign key integrity
        cursor.execute(
            """
            INSERT OR REPLACE INTO runs (
                run_id, week_start, status, total_reviews, analyzed_reviews, avg_rating, coverage_weeks, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                active_run_id,
                week_str,
                "themes_completed",
                len(reviews),
                len(filtered_reviews),
                overall_avg_rating,
                12.0,
                now_iso,
            )
        )

        for t in ranked_themes:
            cursor.execute(
                """
                INSERT OR REPLACE INTO themes (
                    theme_id, run_id, label, description, review_count, share_pct, avg_rating, is_top3
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t["theme_id"],
                    active_run_id,
                    t["label"],
                    t["description"],
                    t["review_count"],
                    t["share_pct"],
                    t["avg_rating"],
                    t["is_top3"],
                )
            )
            # Persist review_themes links
            for rev_id in t["member_review_ids"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO review_themes (review_id, theme_id, distance) VALUES (?, ?, ?)",
                    (rev_id, t["theme_id"], 0.0)
                )
        conn.commit()

    return {
        "run_id": active_run_id,
        "week": week_str,
        "total_input_reviews": len(reviews),
        "analyzable_reviews": len(filtered_reviews),
        "filter_metrics": filter_metrics,
        "cluster_meta": cluster_meta,
        "themes_count": len(ranked_themes),
        "themes": ranked_themes,
        "top_3_themes": [t for t in ranked_themes if t["is_top3"] == 1],
    }

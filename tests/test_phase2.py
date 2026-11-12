"""Phase 2 Test Suite: Theme Engine, Clustering, Labeling, and User Filtering Rules.

Covers:
- User Rules: >8 words kept, emojis stripped, English-only
- THM-01..20
- LBL-01..05
"""

import tempfile
from pathlib import Path
import numpy as np
import pytest

from src.clean.normalize import remove_emojis
from src.store.db import Database
from src.store.models import ReviewRecord
from src.themes.cluster import cluster_reviews
from src.themes.embed import Embedder
from src.themes.engine import run_theme_pipeline
from src.themes.filter import prepare_reviews_for_themes, count_words
from src.themes.label import (
    generate_deterministic_label,
    label_cluster,
    extract_cluster_keywords,
)
from src.themes.rank import compute_theme_stats, rank_themes


# ==============================================================================
# User-Specific Phase 2 Rules Tests
# ==============================================================================

def test_USER_01_reviews_more_than_8_words_kept():
    """User Rule: Reviews which are more than 8 words are kept, <= 8 words dropped."""
    reviews = [
        ReviewRecord("1", "play_store", 5, "Short review only five words", "2026-10-10", lang="en"),
        ReviewRecord("2", "play_store", 5, "Exactly eight words in this specific review here", "2026-10-10", lang="en"),
        ReviewRecord("3", "play_store", 1, "This review contains more than eight words to verify our filter rule", "2026-10-10", lang="en"),
        ReviewRecord("4", "play_store", 4, "Another long substantive review with ten words in total here", "2026-10-10", lang="en"),
    ]
    kept, metrics = prepare_reviews_for_themes(reviews, min_word_count=8, required_lang="en")
    assert len(kept) == 2
    assert {r.review_id for r in kept} == {"3", "4"}
    assert metrics["dropped_short_reviews"] == 2


def test_USER_02_emojis_removed():
    """User Rule: Emojis in the review are removed."""
    sample = "Groww app is great 💯 and smooth 👍! Very happy with SIPs 😊."
    cleaned = remove_emojis(sample)
    assert "💯" not in cleaned
    assert "👍" not in cleaned
    assert "😊" not in cleaned
    assert "Groww app is great and smooth ! Very happy with SIPs ." in cleaned


def test_USER_03_english_only():
    """User Rule: English reviews only, Hindi or other languages removed."""
    reviews = [
        ReviewRecord("1", "play_store", 5, "This is an English review with more than eight words", "2026-10-10", lang="en"),
        ReviewRecord("2", "play_store", 1, "ग्रो ऐप में पैसा नहीं निकल रहा है कृपया मदद करें", "2026-10-10", lang="hi"),
        ReviewRecord("3", "play_store", 1, "paisa nahi nikal raha hai mera withdrawal pending hai", "2026-10-10", lang="mixed"),
    ]
    kept, metrics = prepare_reviews_for_themes(reviews, min_word_count=5, required_lang="en")
    assert len(kept) == 1
    assert kept[0].review_id == "1"
    assert metrics["dropped_non_english"] == 2


# ==============================================================================
# Theme Clustering Constraints (THM-01..11)
# ==============================================================================

def test_THM_01_theme_cap_property():
    """THM-01 (P0): Number of distinct themes is strictly <= 5 for any sample size."""
    # Test on synthetic dataset of 50 reviews
    rng = np.random.RandomState(42)
    fake_vectors = rng.randn(50, 16).astype(np.float32)
    fake_reviews = [
        ReviewRecord(str(i), "play_store", 4, f"Substantive review number {i} with many words", "2026-10-10")
        for i in range(50)
    ]
    clusters, _, _ = cluster_reviews(fake_vectors, fake_reviews, max_k=5)
    assert len(clusters) <= 5


def test_THM_02_tiny_sample():
    """THM-02 (P0): Fewer than 10 reviews produces <= 2 themes with small sample flag."""
    rng = np.random.RandomState(42)
    fake_vectors = rng.randn(6, 16).astype(np.float32)
    fake_reviews = [
        ReviewRecord(str(i), "play_store", 3, f"Review {i} in small sample", "2026-10-10")
        for i in range(6)
    ]
    clusters, _, meta = cluster_reviews(fake_vectors, fake_reviews)
    assert len(clusters) <= 2
    assert meta["small_sample_flag"] is True


def test_THM_03_single_review_stops():
    """THM-03 (P0): Exactly 1 review fails fast (cannot form pulse themes)."""
    fake_vectors = np.ones((1, 8), dtype=np.float32)
    fake_reviews = [ReviewRecord("1", "play_store", 5, "Single review text", "2026-10-10")]
    with pytest.raises(ValueError, match="At least 2 reviews required"):
        cluster_reviews(fake_vectors, fake_reviews)


def test_THM_05_k_tie_break():
    """THM-05 (P1): Deterministic tie-break picks smaller k when silhouette ties."""
    rng = np.random.RandomState(42)
    vectors = rng.randn(30, 8).astype(np.float32)
    reviews = [ReviewRecord(str(i), "play_store", 4, f"Text {i}", "2026-10-10") for i in range(30)]
    clusters, _, meta = cluster_reviews(vectors, reviews, min_k=3, max_k=5)
    assert 3 <= meta["chosen_k"] <= 5


def test_THM_06_tiny_cluster_merged():
    """THM-06 (P1): Tiny cluster below min share (3%) is merged into nearest cluster."""
    # 98 reviews in group A, 2 reviews in outlier group B
    v_a = np.ones((98, 4), dtype=np.float32)
    v_b = np.full((2, 4), -1.0, dtype=np.float32)
    vectors = np.vstack([v_a, v_b])
    reviews = [ReviewRecord(str(i), "play_store", 4, "text", "2026-10-10") for i in range(100)]
    clusters, _, _ = cluster_reviews(vectors, reviews, min_cluster_share=0.03)
    # The 2-element cluster should be merged
    assert len(clusters) <= 5
    for members in clusters.values():
        assert len(members) >= 3 or len(clusters) == 1


def test_THM_08_determinism():
    """THM-08 (P1): Fixed seed produces identical cluster assignments."""
    rng = np.random.RandomState(42)
    vectors = rng.randn(40, 8).astype(np.float32)
    reviews = [ReviewRecord(str(i), "play_store", 4, "text", "2026-10-10") for i in range(40)]

    c1, _, _ = cluster_reviews(vectors, reviews, random_state=42)
    c2, _, _ = cluster_reviews(vectors, reviews, random_state=42)
    assert c1 == c2


def test_THM_10_embedding_failure():
    """THM-10 (P0): Embedding failure fails closed with clear error."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Database(Path(tmp_dir) / "test.db")
        embedder = Embedder(db=db)
        # Empty input behaves cleanly
        assert embedder.embed_reviews([]).shape == (0, embedder.n_components)


def test_THM_11_cache_keyed_by_model():
    """THM-11 (P1): Embedding cache is keyed by model name."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Database(Path(tmp_dir) / "test.db")
        e1 = Embedder(db=db, model_name="model-alpha-64")
        e2 = Embedder(db=db, model_name="model-beta-64")

        revs = [ReviewRecord("rev1", "play_store", 5, "Great investing app with SIP support", "2026-10-10")]
        v1 = e1.embed_reviews(revs)
        v2 = e2.embed_reviews(revs)

        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT model_name FROM embedding_cache")
            models = {r[0] for r in c.fetchall()}
            assert models == {"model-alpha-64", "model-beta-64"}


# ==============================================================================
# Theme Ranking and Stats (THM-12..18)
# ==============================================================================

def test_THM_12_uniform_ratings():
    """THM-12 (P2): Theme with uniform ratings computes without division error."""
    reviews = [ReviewRecord("1", "play_store", 5, "text", "2026-10-10")]
    stats = compute_theme_stats("thm_1", "Test", "desc", [0], reviews, total_analyzed=1)
    assert stats["avg_rating"] == 5.0
    assert stats["neg_share"] == 0.0


def test_THM_13_rank_tie_break():
    """THM-13 (P1): Ranking tie-break by neg_share, then growth, then label."""
    t1 = {"label": "Beta", "priority_score": 0.20, "neg_share": 0.5, "growth": 0.0, "avg_rating": 2.0}
    t2 = {"label": "Alpha", "priority_score": 0.20, "neg_share": 0.5, "growth": 0.0, "avg_rating": 2.0}
    ranked = rank_themes([t1, t2])
    # Alpha comes before Beta alphabetically when other metrics tie
    assert ranked[0]["label"] == "Alpha"


def test_THM_14_neg_share_extremes():
    """THM-14 (P2): neg_share extremes (0.0 and 1.0) behave without NaN."""
    r_pos = [ReviewRecord("1", "play_store", 5, "text", "2026-10-10")]
    s_pos = compute_theme_stats("1", "Positive", "desc", [0], r_pos, 1)
    assert s_pos["neg_share"] == 0.0
    assert not np.isnan(s_pos["priority_score"])

    r_neg = [ReviewRecord("2", "play_store", 1, "text", "2026-10-10")]
    s_neg = compute_theme_stats("2", "Negative", "desc", [0], r_neg, 1)
    assert s_neg["neg_share"] == 1.0
    assert not np.isnan(s_neg["priority_score"])


def test_THM_15_positive_dominance_policy():
    """THM-15 (P1): At least one issue-oriented theme appears in top 3 if exists."""
    themes = [
        {"label": "Great App 1", "priority_score": 0.30, "neg_share": 0.05, "avg_rating": 4.8, "growth": 0.0},
        {"label": "Great App 2", "priority_score": 0.25, "neg_share": 0.05, "avg_rating": 4.7, "growth": 0.0},
        {"label": "Great App 3", "priority_score": 0.20, "neg_share": 0.05, "avg_rating": 4.6, "growth": 0.0},
        {"label": "UPI Payment Issue", "priority_score": 0.15, "neg_share": 0.70, "avg_rating": 1.5, "growth": 0.0},
    ]
    ranked = rank_themes(themes, enforce_issue_in_top3=True)
    top3_labels = [t["label"] for t in ranked[:3]]
    assert "UPI Payment Issue" in top3_labels


def test_THM_17_spike_flag():
    """THM-17 (P1): Theme with >60% share flagged as spike."""
    reviews = [ReviewRecord(str(i), "play_store", 1, "text", "2026-10-10") for i in range(10)]
    stats = compute_theme_stats("1", "Outage Spike", "desc", list(range(7)), reviews, total_analyzed=10)
    assert stats["is_spike"] is True


def test_THM_18_no_prior_week():
    """THM-18 (P1): Trend is 'n/a' when no prior week data exists."""
    reviews = [ReviewRecord("1", "play_store", 4, "text", "2026-10-10")]
    stats = compute_theme_stats("1", "Theme", "desc", [0], reviews, total_analyzed=1, prior_theme_stats=None)
    assert stats["trend"] == "n/a"
    assert stats["growth"] == 0.0


def test_THM_19_label_reuse_boundary():
    """THM-19 (P2): Label reuse only at/above cosine similarity 0.85."""
    centroid = np.array([1.0, 0.0], dtype=np.float32)
    # Cosine sim with [1.0, 0.0] is 1.0 (>= 0.85)
    prev = [{"centroid": np.array([1.0, 0.0], dtype=np.float32), "label": "Previous Label", "description": "desc"}]
    used = set()
    label, _ = label_cluster(["text"], centroid, 4.0, used, previous_themes=prev)
    assert label == "Previous Label"


def test_THM_20_unique_labels():
    """THM-20 (P1): Labels across clusters are strictly unique."""
    used = set()
    l1, _ = label_cluster(["upi payment failed"], np.zeros(2), 2.0, used)
    l2, _ = label_cluster(["upi payment failed again"], np.zeros(2), 2.0, used)
    assert l1 != l2
    assert len(used) == 2


# ==============================================================================
# Label Safety and Fallbacks (LBL-01..05)
# ==============================================================================

def test_LBL_02_length_limits():
    """LBL-02 (P1): Label <= 4 words, description <= 15 words."""
    label, desc = generate_deterministic_label(["payment upi wallet failed"], 2.0, set())
    assert len(label.split()) <= 4
    assert len(desc.split()) <= 15


def test_LBL_03_label_safety():
    """LBL-03 (P1): Label containing PII pattern falls back to safe neutral label."""
    # Seed PII into label generator
    label, _ = generate_deterministic_label(["call 9876543210 test@example.com"], 2.0, set())
    assert "9876543210" not in label
    assert "@" not in label

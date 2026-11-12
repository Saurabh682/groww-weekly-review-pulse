"""Review embedding generation and SQLite caching (THM-10, THM-11)."""

import json
import sqlite3
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from src.store.db import Database
from src.store.models import ReviewRecord


CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS embedding_cache (
    review_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    vector_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, model_name)
);
"""


class Embedder:
    """Deterministic, cached vector embedder for reviews."""

    def __init__(
        self,
        db: Database,
        model_name: str = "tfidf-lsa-128",
        n_components: int = 64
    ):
        self.db = db
        self.model_name = model_name
        self.n_components = n_components
        self._init_cache_table()

    def _init_cache_table(self) -> None:
        with self.db.get_connection() as conn:
            conn.executescript(CACHE_TABLE_SQL)

    def _get_cached_vectors(self, review_ids: List[str]) -> Dict[str, np.ndarray]:
        if not review_ids:
            return {}

        cached: Dict[str, np.ndarray] = {}
        # Fetch in batches
        placeholders = ",".join("?" for _ in review_ids)
        query = f"SELECT review_id, vector_json FROM embedding_cache WHERE model_name = ? AND review_id IN ({placeholders})"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, [self.model_name] + review_ids)
            for row in cursor.fetchall():
                cached[row["review_id"]] = np.array(json.loads(row["vector_json"]), dtype=np.float32)

        return cached

    def _save_cached_vectors(self, items: List[Tuple[str, np.ndarray]]) -> None:
        if not items:
            return
        query = "INSERT OR REPLACE INTO embedding_cache (review_id, model_name, vector_json) VALUES (?, ?, ?)"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                query,
                [(rev_id, self.model_name, json.dumps(vec.tolist())) for rev_id, vec in items]
            )
            conn.commit()

    def embed_reviews(self, reviews: List[ReviewRecord]) -> np.ndarray:
        """Compute normalized vector embeddings for given reviews with SQLite caching (THM-11)."""
        if not reviews:
            return np.empty((0, self.n_components), dtype=np.float32)

        review_ids = [r.review_id for r in reviews]
        cached_map = self._get_cached_vectors(review_ids)

        uncached_indices = [i for i, r in enumerate(reviews) if r.review_id not in cached_map]

        if not uncached_indices:
            # All vectors were cached
            return np.array([cached_map[r.review_id] for r in reviews], dtype=np.float32)

        # Generate vectors for reviews
        texts = [r.text for r in reviews]
        try:
            # TF-IDF + TruncatedSVD for semantic dimension reduction
            tfidf = TfidfVectorizer(
                max_features=2500,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
            )
            tfidf_matrix = tfidf.fit_transform(texts)

            components = min(self.n_components, tfidf_matrix.shape[1], max(1, len(texts) - 1))
            if components > 1:
                svd = TruncatedSVD(n_components=components, random_state=42)
                dense_matrix = svd.fit_transform(tfidf_matrix)
            else:
                dense_matrix = tfidf_matrix.toarray()

            normalized_vectors = normalize(dense_matrix, norm="l2", axis=1).astype(np.float32)

        except Exception as exc:
            raise RuntimeError(f"Embedding generation failed: {exc} (THM-10)") from exc

        # Save to cache
        to_cache = [
            (reviews[i].review_id, normalized_vectors[i])
            for i in uncached_indices
        ]
        self._save_cached_vectors(to_cache)

        return normalized_vectors

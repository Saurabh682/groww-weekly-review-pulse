from typing import List

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.store.models import ReviewRecord

VECTOR_SIZE = 64


def embed_reviews(reviews: List[ReviewRecord]) -> np.ndarray:
    if not reviews:
        return np.empty((0, VECTOR_SIZE), dtype=np.float32)
    try:
        tfidf = TfidfVectorizer(max_features=2500, stop_words="english", ngram_range=(1, 2), min_df=1)
        weights = tfidf.fit_transform([r.text for r in reviews])
        size = min(VECTOR_SIZE, weights.shape[1], max(1, len(reviews) - 1))
        dense = TruncatedSVD(n_components=size, random_state=42).fit_transform(weights) if size > 1 else weights.toarray()
        return normalize(dense, norm="l2", axis=1).astype(np.float32)
    except Exception as exc:
        raise RuntimeError(f"Embedding generation failed: {exc} (THM-10)") from exc

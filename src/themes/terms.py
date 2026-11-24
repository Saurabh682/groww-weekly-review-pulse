from typing import Any, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer


def highest_first(values: np.ndarray) -> np.ndarray:
    return np.argsort(-values, kind="stable")


def weigh_terms(texts: List[str], limit: int) -> Tuple[Any, np.ndarray]:
    counter = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    counts = counter.fit_transform(texts)
    kept = np.sort(highest_first(np.asarray(counts.sum(axis=0)).ravel())[:limit])
    return TfidfTransformer().fit_transform(counts[:, kept]), counter.get_feature_names_out()[kept]

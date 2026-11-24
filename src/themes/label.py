"""Theme labeling engine with LLM extraction and deterministic fallback (LBL-01..05, THM-19, THM-20)."""

import re
from typing import List, Optional, Set, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.clean.pii import scrub_pii
from src.domains.pack import DomainPack
from src.themes.terms import highest_first, weigh_terms

MAX_LABEL_TERMS = 100


def extract_cluster_keywords(texts: List[str], top_n: int = 5) -> List[str]:
    """Extract top distinctive keywords from a cluster of texts using TF-IDF."""
    if not texts:
        return ["General Feedback"]

    try:
        weights, terms = weigh_terms(texts, MAX_LABEL_TERMS)
        scores = np.asarray(weights.sum(axis=0)).ravel()
        keywords = [terms[i].title() for i in highest_first(scores)[:top_n]]
        return keywords if keywords else ["User Experience"]
    except Exception:
        # Fallback if text is very sparse
        words = re.findall(r"\b[A-Za-z]{4,}\b", " ".join(texts).lower())
        from collections import Counter
        common = [w.title() for w, _ in Counter(words).most_common(top_n)]
        return common or ["General Feedback"]


def generate_deterministic_label(
    texts: List[str],
    avg_rating: float,
    used_labels: Set[str],
    pack: DomainPack,
) -> Tuple[str, str]:
    """Fallback rule-based labeling using scoring across domain categories and TF-IDF (LBL-01, LBL-04)."""
    joined = " ".join(texts).lower()

    categories = pack.label_keywords

    # Score each category based on keyword density
    scores = {}
    for cat, keywords in categories.items():
        score = sum(joined.count(kw) for kw in keywords)
        scores[cat] = score

    # Sort categories by score descending
    sorted_cats = sorted(scores.items(), key=lambda x: -x[1])

    candidate_label = None
    for cat, score in sorted_cats:
        if score > 0 and cat not in used_labels:
            candidate_label = cat
            break

    # If no unused domain category scored, or score is 0, use TF-IDF keywords
    if not candidate_label:
        kw = extract_cluster_keywords(texts, top_n=2)
        candidate_label = " & ".join(kw[:2])

    # Disambiguate if already used (THM-20)
    final_label = candidate_label
    counter = 2
    while final_label in used_labels:
        final_label = f"{candidate_label} {counter}"
        counter += 1

    # Length limit: label <= 4 words (LBL-02)
    label_words = final_label.split()
    if len(label_words) > 4:
        final_label = " ".join(label_words[:4])

    # PII safety check on label (LBL-03)
    pii_check = scrub_pii(final_label)
    if pii_check.pii_found:
        final_label = "Platform Feedback"

    description = f"User feedback regarding {final_label.lower()}."
    desc_words = description.split()
    if len(desc_words) > 15:
        description = " ".join(desc_words[:15])

    return final_label, description


def label_cluster(
    cluster_texts: List[str],
    cluster_centroid: np.ndarray,
    avg_rating: float,
    used_labels: Set[str],
    pack: DomainPack,
    previous_themes: Optional[List[dict]] = None
) -> Tuple[str, str]:
    """Assign a human-readable label (<=4 words) and description (<=15 words) to a theme.
    
    Checks:
    - Stability: Reuse previous label if cosine similarity >= 0.85 (THM-19)
    - Uniqueness: Ensure labels are distinct (THM-20)
    - PII Safety: Filter out any PII (LBL-03)
    - Enforces length caps: <=4 words label, <=15 words description (LBL-02)
    """
    # 1. Label Reuse check (THM-19)
    if previous_themes:
        for prev in previous_themes:
            prev_vec = prev.get("centroid")
            prev_label = prev.get("label")
            if prev_vec is not None and prev_label and prev_label not in used_labels:
                sim = float(cosine_similarity(
                    cluster_centroid.reshape(1, -1),
                    prev_vec.reshape(1, -1)
                )[0][0])
                if sim >= 0.85:
                    used_labels.add(prev_label)
                    return prev_label, prev.get("description", f"User issues relating to {prev_label.lower()}.")

    # 2. Generate deterministic fallback/baseline
    label, desc = generate_deterministic_label(cluster_texts, avg_rating, used_labels, pack)
    used_labels.add(label)

    return label, desc

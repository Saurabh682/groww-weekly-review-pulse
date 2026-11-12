"""Capped clustering engine with silhouette selection and size guards (THM-01..09)."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_distances

from src.store.models import ReviewRecord


def cluster_reviews(
    vectors: np.ndarray,
    reviews: List[ReviewRecord],
    min_k: int = 3,
    max_k: int = 5,
    min_cluster_share: float = 0.03,
    random_state: int = 42
) -> Tuple[Dict[int, List[int]], np.ndarray, dict]:
    """Cluster reviews into at most 5 themes (THM-01) with deterministic silhouette selection (THM-05).
    
    Returns:
    - clusters: dict mapping cluster_idx -> list of review indices
    - centroids: 2D numpy array of cluster centroids
    - metadata: dict with silhouette score, chosen_k, sample_flag, etc.
    """
    n_samples = len(reviews)

    # 1. Edge Case: 1 review (THM-03)
    if n_samples <= 1:
        raise ValueError(
            f"Cannot form themes from {n_samples} review. At least 2 reviews required (THM-03)."
        )

    # 2. Edge Case: Tiny sample < 10 reviews (THM-02)
    if n_samples < 10:
        target_k = min(2, n_samples)
        kmeans = KMeans(n_clusters=target_k, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(vectors)
        centroids = kmeans.cluster_centers_

        clusters: Dict[int, List[int]] = {}
        for idx, lbl in enumerate(labels):
            clusters.setdefault(lbl, []).append(idx)

        assert len(clusters) <= 5, "Hard constraint violated: themes > 5 (THM-01)"
        return clusters, centroids, {
            "chosen_k": target_k,
            "silhouette": 0.0,
            "small_sample_flag": True,
            "note": "Very small sample (<10 reviews); clustering constrained to <=2 themes (THM-02)",
        }

    # 3. Candidate k evaluation: k in [min_k, min(max_k, n_samples - 1)] (THM-01, THM-05)
    effective_max_k = min(max_k, n_samples - 1)
    effective_min_k = min(min_k, effective_max_k)

    best_k = effective_min_k
    best_score = -1.0
    best_kmeans: Optional[KMeans] = None

    # Check for identical/collinear vectors (THM-04)
    for k in range(effective_min_k, effective_max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(vectors)

        # Ensure at least 2 distinct labels exist for silhouette computation
        unique_labels = set(labels)
        if len(unique_labels) < 2:
            continue

        try:
            score = float(silhouette_score(vectors, labels, metric="cosine"))
        except Exception:
            score = 0.0

        # Deterministic tie-break: strictly greater score required to increase k (smaller k on tie THM-05)
        if score > best_score:
            best_score = score
            best_k = k
            best_kmeans = kmeans

    if best_kmeans is None:
        best_kmeans = KMeans(n_clusters=effective_min_k, random_state=random_state, n_init=10)
        best_kmeans.fit(vectors)

    labels = best_kmeans.labels_
    centroids = best_kmeans.cluster_centers_

    # Build initial cluster mapping
    initial_clusters: Dict[int, List[int]] = {}
    for idx, lbl in enumerate(labels):
        initial_clusters.setdefault(lbl, []).append(idx)

    # 4. Tiny Cluster Merge (THM-06)
    # Merges any cluster with share < min_cluster_share into the nearest centroid
    min_count = max(1, int(n_samples * min_cluster_share))
    valid_clusters: Dict[int, List[int]] = {}
    tiny_clusters: List[int] = []

    for c_id, members in initial_clusters.items():
        if len(members) >= min_count or len(initial_clusters) <= 1:
            valid_clusters[c_id] = members
        else:
            tiny_clusters.append(c_id)

    if tiny_clusters and valid_clusters:
        valid_ids = list(valid_clusters.keys())
        valid_centroids = centroids[valid_ids]

        for tiny_id in tiny_clusters:
            tiny_members = initial_clusters[tiny_id]
            tiny_centroid = centroids[tiny_id].reshape(1, -1)
            # Find closest valid centroid
            distances = cosine_distances(tiny_centroid, valid_centroids)[0]
            closest_idx = int(np.argmin(distances))
            closest_valid_id = valid_ids[closest_idx]
            valid_clusters[closest_valid_id].extend(tiny_members)

    # Remap cluster IDs to contiguous 0..N-1
    final_clusters: Dict[int, List[int]] = {}
    final_centroid_list: List[np.ndarray] = []

    for new_id, (old_id, members) in enumerate(valid_clusters.items()):
        final_clusters[new_id] = members
        # Recompute centroid of merged cluster
        member_vectors = vectors[members]
        new_centroid = np.mean(member_vectors, axis=0)
        norm = np.linalg.norm(new_centroid)
        if norm > 0:
            new_centroid = new_centroid / norm
        final_centroid_list.append(new_centroid)

    final_centroids = np.array(final_centroid_list, dtype=np.float32)

    # Hard assert cap of <= 5 (THM-01)
    assert len(final_clusters) <= 5, f"Hard constraint failed: {len(final_clusters)} > 5 themes"

    return final_clusters, final_centroids, {
        "chosen_k": len(final_clusters),
        "silhouette": round(best_score, 4),
        "small_sample_flag": False,
        "note": "Clustering complete under <= 5 theme cap",
    }

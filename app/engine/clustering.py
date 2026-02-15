import logging

import numpy as np
from sklearn.cluster import DBSCAN

from app.config import settings

logger = logging.getLogger(__name__)


def cluster_embeddings(
    embeddings: list[list[float]],
    doc_ids: list[str],
) -> list[dict]:
    """Cluster documents by embedding similarity using DBSCAN.

    Returns a list of clusters, each with:
        - cluster_id: int
        - doc_ids: list[str]
        - centroid: np.ndarray (mean embedding of cluster)
    """
    if len(embeddings) < settings.MIN_CLUSTER_SIZE:
        return []

    matrix = np.array(embeddings, dtype=np.float32)

    # Normalize for cosine-like behavior with euclidean distance
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = matrix / norms

    # eps=0.55 on normalized vectors ≈ cosine_similarity threshold of 0.85
    # (cosine_distance = 1 - sim; euclidean on unit vectors ≈ sqrt(2 * cosine_distance))
    clusterer = DBSCAN(
        eps=0.55,
        min_samples=settings.MIN_CLUSTER_SIZE,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(normalized)

    # Group by cluster label (ignore noise: label == -1)
    clusters_map: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue
        clusters_map.setdefault(label, []).append(idx)

    clusters = []
    for cluster_id, indices in clusters_map.items():
        cluster_doc_ids = [doc_ids[i] for i in indices]
        centroid = normalized[indices].mean(axis=0)
        clusters.append({
            "cluster_id": cluster_id,
            "doc_ids": cluster_doc_ids,
            "centroid": centroid,
        })

    logger.info("Found %d clusters from %d documents", len(clusters), len(embeddings))
    return clusters

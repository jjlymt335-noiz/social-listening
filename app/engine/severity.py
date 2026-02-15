from app.config import settings


def compute_severity(cluster_size: int, neg_ratio: float) -> str:
    """Compute event severity based on cluster size and negative ratio.

    Returns: "P0", "P1", or "P2"
    """
    if cluster_size > settings.P0_CLUSTER_SIZE and neg_ratio > settings.P0_NEG_RATIO:
        return "P0"
    if cluster_size > settings.P1_CLUSTER_SIZE:
        return "P1"
    return "P2"

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document
from app.models.event import Event
from app.models.event_doc import EventDoc

logger = logging.getLogger(__name__)


async def get_active_events(brand: str, session: AsyncSession) -> list[Event]:
    """Get events within the 12h lifecycle window for a brand."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.EVENT_LIFECYCLE_HOURS)
    stmt = (
        select(Event)
        .where(Event.brand == brand)
        .where(Event.status.in_(["open", "monitoring", "cooling"]))
        .where(Event.last_update_time >= cutoff)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_event_centroid(event_id: str, session: AsyncSession) -> np.ndarray | None:
    """Compute the centroid embedding of an event's documents."""
    stmt = (
        select(Document.embedding)
        .join(EventDoc, EventDoc.doc_id == Document.doc_id)
        .where(EventDoc.event_id == event_id)
    )
    result = await session.execute(stmt)
    embeddings = [row[0] for row in result.all() if row[0] is not None]
    if not embeddings:
        return None
    return np.mean(np.array(embeddings), axis=0)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def find_matching_event(
    cluster_centroid: np.ndarray,
    cluster_docs: list[dict],
    active_events: list[Event],
    session: AsyncSession,
) -> Event | None:
    """Find an active event that matches the cluster.

    Hard merge rules checked first, then cosine similarity.
    Returns the matching event or None.
    """
    # Hard merge: check for exact attribute matches
    # (flight_number, airline+route, policy_country+policy_type, system_error keyword)
    # These would require document metadata fields; for now rely on embedding similarity.

    best_match: Event | None = None
    best_sim = 0.0

    for event in active_events:
        event_centroid = await get_event_centroid(event.event_id, session)
        if event_centroid is None:
            continue

        sim = cosine_similarity(cluster_centroid, event_centroid)
        if sim >= settings.EMBEDDING_SIM_THRESHOLD and sim > best_sim:
            best_sim = sim
            best_match = event

    if best_match:
        logger.info("Matched cluster to event %s (sim=%.3f)", best_match.event_id, best_sim)

    return best_match

"""Short-Term Event Engine.

Runs every 30 minutes:
1. Fetch documents from last 6 hours
2. Group by brand
3. Detect clusters (HDBSCAN)
4. Match against active events (within 12h lifecycle)
5. Merge or create event
6. Update event states
"""

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.clustering import cluster_embeddings
from app.engine.event_matcher import find_matching_event, get_active_events
from app.engine.severity import compute_severity
from app.models.document import Document
from app.models.event import Event
from app.models.event_doc import EventDoc

logger = logging.getLogger(__name__)


async def run_short_term_engine(session: AsyncSession) -> None:
    """Execute one cycle of the short-term event engine."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=settings.SHORT_TERM_AGG_WINDOW_HOURS)

    # Fetch recent documents
    stmt = select(Document).where(Document.created_at >= window_start)
    result = await session.execute(stmt)
    docs = list(result.scalars().all())

    if not docs:
        logger.info("No documents in the last %dh window", settings.SHORT_TERM_AGG_WINDOW_HOURS)
        return

    # Group by brand
    brands: dict[str, list[Document]] = {}
    for doc in docs:
        brands.setdefault(doc.brand, []).append(doc)

    for brand, brand_docs in brands.items():
        await _process_brand(brand, brand_docs, session, now)

    # Update lifecycle states for all events
    await _update_event_states(session, now)
    await session.commit()


async def _process_brand(
    brand: str,
    docs: list[Document],
    session: AsyncSession,
    now: datetime,
) -> None:
    """Process clustering and event matching for a single brand."""
    embeddings = [doc.embedding for doc in docs if doc.embedding is not None]
    doc_ids = [doc.doc_id for doc in docs if doc.embedding is not None]

    if len(embeddings) < settings.MIN_CLUSTER_SIZE:
        return

    clusters = cluster_embeddings(embeddings, doc_ids)
    if not clusters:
        return

    active_events = await get_active_events(brand, session)

    for cluster in clusters:
        cluster_doc_ids = cluster["doc_ids"]
        centroid = cluster["centroid"]

        # Gather cluster stats
        cluster_docs = [d for d in docs if d.doc_id in set(cluster_doc_ids)]
        neg_count = sum(1 for d in cluster_docs if d.sentiment == "neg")
        neg_ratio = neg_count / len(cluster_docs) if cluster_docs else 0.0

        # Determine dominant region
        region_counts = Counter(d.region_group for d in cluster_docs)
        dominant_region = region_counts.most_common(1)[0][0] if region_counts else None

        # Try to match with existing event
        matched_event = await find_matching_event(centroid, cluster_docs, active_events, session)

        if matched_event:
            # Merge into existing event
            matched_event.cluster_size += len(cluster_doc_ids)
            matched_event.neg_ratio = neg_ratio
            matched_event.last_update_time = now
            matched_event.status = "monitoring"
            matched_event.severity = compute_severity(matched_event.cluster_size, neg_ratio)

            for doc_id in cluster_doc_ids:
                existing = await session.execute(
                    select(EventDoc).where(
                        EventDoc.event_id == matched_event.event_id,
                        EventDoc.doc_id == doc_id,
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(EventDoc(event_id=matched_event.event_id, doc_id=doc_id))

            logger.info("Merged %d docs into event %s", len(cluster_doc_ids), matched_event.event_id)
        else:
            # Create new event
            event_id = str(uuid.uuid4())
            severity = compute_severity(len(cluster_doc_ids), neg_ratio)

            event = Event(
                event_id=event_id,
                brand=brand,
                event_type="A",  # Default; could be refined by analysis
                severity=severity,
                status="open",
                start_time=now,
                last_update_time=now,
                cluster_size=len(cluster_doc_ids),
                neg_ratio=neg_ratio,
                region_group=dominant_region,
            )
            session.add(event)

            for doc_id in cluster_doc_ids:
                session.add(EventDoc(event_id=event_id, doc_id=doc_id))

            logger.info("Created new event %s (size=%d, severity=%s)", event_id, len(cluster_doc_ids), severity)


async def _update_event_states(session: AsyncSession, now: datetime) -> None:
    """Update event lifecycle states: monitoring -> cooling -> closed."""
    cooling_cutoff = now - timedelta(hours=settings.EVENT_COOLING_THRESHOLD_HOURS)
    lifecycle_cutoff = now - timedelta(hours=settings.EVENT_LIFECYCLE_HOURS)

    stmt = select(Event).where(Event.status.in_(["open", "monitoring", "cooling"]))
    result = await session.execute(stmt)
    events = result.scalars().all()

    for event in events:
        if event.last_update_time <= lifecycle_cutoff:
            event.status = "closed"
            logger.info("Event %s closed (lifecycle expired)", event.event_id)
        elif event.last_update_time <= cooling_cutoff:
            if event.status != "cooling":
                event.status = "cooling"
                logger.info("Event %s moved to cooling", event.event_id)

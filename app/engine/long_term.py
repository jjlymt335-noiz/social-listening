"""Long-Term Trend Engine.

Runs once daily (00:00 UTC):
- Aggregate daily volume / sentiment counts per brand
- Aggregate daily aspect metrics per brand
- Store in daily_metrics / daily_aspect_metrics
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.metrics import DailyAspectMetrics, DailyMetrics

logger = logging.getLogger(__name__)


async def run_long_term_engine(session: AsyncSession, target_date: date | None = None) -> None:
    """Aggregate metrics for a given date (defaults to yesterday)."""
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    await _aggregate_daily_metrics(session, target_date, day_start, day_end)
    await _aggregate_aspect_metrics(session, target_date, day_start, day_end)
    await session.commit()

    logger.info("Long-term aggregation completed for %s", target_date)


async def _aggregate_daily_metrics(
    session: AsyncSession,
    target_date: date,
    day_start: datetime,
    day_end: datetime,
) -> None:
    """Aggregate volume and sentiment counts per brand."""
    stmt = (
        select(
            Document.brand,
            func.count().label("volume_total"),
        )
        .where(Document.created_at >= day_start)
        .where(Document.created_at < day_end)
        .group_by(Document.brand)
    )
    result = await session.execute(stmt)

    for row in result.all():
        brand = row.brand
        # Count sentiments separately for SQLite compatibility
        pos_q = await session.execute(
            select(func.count()).where(
                Document.brand == brand, Document.created_at >= day_start,
                Document.created_at < day_end, Document.sentiment == "pos",
            )
        )
        neu_q = await session.execute(
            select(func.count()).where(
                Document.brand == brand, Document.created_at >= day_start,
                Document.created_at < day_end, Document.sentiment == "neu",
            )
        )
        neg_q = await session.execute(
            select(func.count()).where(
                Document.brand == brand, Document.created_at >= day_start,
                Document.created_at < day_end, Document.sentiment == "neg",
            )
        )

        # Delete + insert (SQLite-compatible upsert)
        await session.execute(
            delete(DailyMetrics).where(DailyMetrics.brand == brand, DailyMetrics.date == target_date)
        )
        session.add(DailyMetrics(
            date=target_date, brand=brand, volume_total=row.volume_total,
            pos_count=pos_q.scalar() or 0, neu_count=neu_q.scalar() or 0, neg_count=neg_q.scalar() or 0,
        ))


async def _aggregate_aspect_metrics(
    session: AsyncSession,
    target_date: date,
    day_start: datetime,
    day_end: datetime,
) -> None:
    """Aggregate volume and negative counts per brand+aspect."""
    stmt = (
        select(Document.brand, Document.aspect, func.count().label("volume"))
        .where(Document.created_at >= day_start)
        .where(Document.created_at < day_end)
        .where(Document.aspect.isnot(None))
        .group_by(Document.brand, Document.aspect)
    )
    result = await session.execute(stmt)

    for row in result.all():
        neg_q = await session.execute(
            select(func.count()).where(
                Document.brand == row.brand, Document.aspect == row.aspect,
                Document.created_at >= day_start, Document.created_at < day_end,
                Document.sentiment == "neg",
            )
        )
        await session.execute(
            delete(DailyAspectMetrics).where(
                DailyAspectMetrics.brand == row.brand,
                DailyAspectMetrics.date == target_date,
                DailyAspectMetrics.aspect == row.aspect,
            )
        )
        session.add(DailyAspectMetrics(
            date=target_date, brand=row.brand, aspect=row.aspect,
            volume=row.volume, neg_count=neg_q.scalar() or 0,
        ))

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.metrics import DailyAspectMetrics, DailyMetrics
from app.schemas.metrics import DailyAspectMetricsResponse, DailyMetricsResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/daily", response_model=list[DailyMetricsResponse])
async def get_daily_metrics(
    brand: str = Query(..., description="Brand name"),
    limit: int = Query(30, ge=1, le=90, description="Number of days"),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(DailyMetrics)
        .where(DailyMetrics.brand == brand)
        .order_by(DailyMetrics.date.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/aspect", response_model=list[DailyAspectMetricsResponse])
async def get_aspect_metrics(
    brand: str = Query(..., description="Brand name"),
    limit: int = Query(30, ge=1, le=90, description="Number of days"),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(DailyAspectMetrics)
        .where(DailyAspectMetrics.brand == brand)
        .order_by(DailyAspectMetrics.date.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

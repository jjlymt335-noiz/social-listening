from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.document import Document
from app.models.event import Event
from app.models.event_doc import EventDoc
from app.schemas.event import EventDocResponse, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/docs-by-aspect", response_model=list[EventDocResponse])
async def get_docs_by_aspect(
    brand: str = Query(..., description="Brand name"),
    aspect: str = Query(..., description="Aspect to filter by"),
    sentiment: str | None = Query(None, description="Filter by sentiment (pos/neu/neg)"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Get documents filtered by aspect, optionally by sentiment."""
    stmt = (
        select(Document)
        .where(Document.brand == brand, Document.aspect == aspect)
        .order_by(Document.created_at.desc())
        .limit(limit)
    )
    if sentiment:
        stmt = stmt.where(Document.sentiment == sentiment)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("", response_model=list[EventResponse])
async def list_events(
    brand: str = Query(..., description="Brand name"),
    status: str | None = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Event).where(Event.brand == brand).order_by(Event.last_update_time.desc())
    if status:
        stmt = stmt.where(Event.status == status)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Event).where(Event.event_id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/docs", response_model=list[EventDocResponse])
async def get_event_docs(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    # Verify event exists
    event_result = await session.execute(select(Event).where(Event.event_id == event_id))
    if not event_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    stmt = (
        select(Document)
        .join(EventDoc, EventDoc.doc_id == Document.doc_id)
        .where(EventDoc.event_id == event_id)
        .order_by(Document.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()

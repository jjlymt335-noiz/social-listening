from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(1), nullable=False)  # A/B/C/D/E
    severity: Mapped[str] = mapped_column(String(2), nullable=False)  # P0/P1/P2
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cluster_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neg_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    region_group: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("idx_events_brand_status", "brand", "status"),
        Index("idx_events_last_update", "last_update_time"),
    )

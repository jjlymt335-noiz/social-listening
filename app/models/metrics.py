from datetime import date

from sqlalchemy import Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    volume_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pos_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neu_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neg_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_daily_metrics_brand_date", "brand", "date", unique=True),
    )


class DailyAspectMetrics(Base):
    __tablename__ = "daily_aspect_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    aspect: Mapped[str] = mapped_column(String(100), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neg_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_daily_aspect_brand_date", "brand", "date", "aspect", unique=True),
    )

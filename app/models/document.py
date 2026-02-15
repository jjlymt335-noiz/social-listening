import json
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    region_group: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    text_clean: Mapped[str] = mapped_column(Text, nullable=False)
    topic_l1: Mapped[str | None] = mapped_column(String(100))
    aspect: Mapped[str | None] = mapped_column(String(100))
    sentiment: Mapped[str] = mapped_column(String(3), nullable=False)  # pos/neu/neg
    intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_cn: Mapped[str | None] = mapped_column(Text)  # Chinese summary
    embedding_json: Mapped[str | None] = mapped_column(Text)  # JSON-serialized vector
    engagement_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("idx_docs_brand_created", "brand", "created_at"),
        Index("idx_docs_country", "country_code"),
    )

    @property
    def embedding(self) -> list[float] | None:
        if self.embedding_json is None:
            return None
        return json.loads(self.embedding_json)

    @embedding.setter
    def embedding(self, value: list[float] | None) -> None:
        if value is None:
            self.embedding_json = None
        else:
            self.embedding_json = json.dumps(value)

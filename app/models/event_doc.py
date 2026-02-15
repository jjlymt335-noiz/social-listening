from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EventDoc(Base):
    __tablename__ = "event_docs"

    event_id: Mapped[str] = mapped_column(String(255), ForeignKey("events.event_id"), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.doc_id"), primary_key=True)

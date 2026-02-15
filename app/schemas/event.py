from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    event_id: str
    brand: str
    event_type: str
    severity: str
    status: str
    start_time: datetime
    last_update_time: datetime
    cluster_size: int
    neg_ratio: float
    region_group: str | None
    summary: str | None

    model_config = {"from_attributes": True}


class EventDocResponse(BaseModel):
    doc_id: str
    brand: str
    platform: str
    created_at: datetime
    country_code: str
    text_clean: str
    summary_cn: str | None = None
    topic_l1: str | None = None
    aspect: str | None = None
    sentiment: str
    intensity: int
    engagement_count: int = 0

    model_config = {"from_attributes": True}

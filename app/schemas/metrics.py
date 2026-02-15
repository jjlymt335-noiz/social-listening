from datetime import date

from pydantic import BaseModel


class DailyMetricsResponse(BaseModel):
    date: date
    brand: str
    volume_total: int
    pos_count: int
    neu_count: int
    neg_count: int

    model_config = {"from_attributes": True}


class DailyAspectMetricsResponse(BaseModel):
    date: date
    brand: str
    aspect: str
    volume: int
    neg_count: int

    model_config = {"from_attributes": True}

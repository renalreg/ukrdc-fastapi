import datetime

from pydantic import Field

from .base import OrmModel


class HistoryPoint(OrmModel):
    time: datetime.date = Field(..., description="Timestamp (x-axis)")
    count: int = Field(..., description="Count (y-axis)")

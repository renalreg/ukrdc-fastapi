import datetime

from pydantic import Field

from .base import OrmModel


class HistoryPoint(OrmModel):
    """Single point of time-series data"""

    time: datetime.date = Field(..., description="Timestamp (x-axis)")
    count: int = Field(..., description="Count (y-axis)")

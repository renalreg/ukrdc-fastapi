import datetime

from .base import OrmModel


class HistoryPoint(OrmModel):
    time: datetime.date
    count: int

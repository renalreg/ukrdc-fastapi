import datetime
from typing import Any

from sqlalchemy.orm.query import Query

from ukrdc_fastapi.schemas.base import OrmModel


class TotalDayPrev(OrmModel):
    total: int
    day: int
    prev: int


def total_day_prev(query: Query, table: Any, datefield: str) -> TotalDayPrev:
    """Create a summary of total results, new today, and new previous day from
    an SQLAlchemy query

    Args:
        query (Query): Base SQLAlchemy query
        table (Any): Table base class
        datefield (str): Datetime field name

    Returns:
        dict[str, int]: Summary of total, day, and prev
    """
    total_workitems = query.count()
    day_workitems = query.filter(
        getattr(table, datefield)
        > (datetime.datetime.utcnow() - datetime.timedelta(days=1))
    ).count()
    prev_workitems = query.filter(
        getattr(table, datefield)
        > (datetime.datetime.utcnow() - datetime.timedelta(days=2)),
        getattr(table, datefield)
        <= (datetime.datetime.utcnow() - datetime.timedelta(days=1)),
    ).count()
    return TotalDayPrev(
        **{
            "total": total_workitems,
            "day": day_workitems,
            "prev": prev_workitems,
        }
    )

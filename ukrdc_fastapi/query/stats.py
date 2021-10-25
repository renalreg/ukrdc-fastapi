import datetime
from typing import Optional

from sqlalchemy.orm.session import Session
from ukrdc_sqla.stats import ErrorHistory

from ukrdc_fastapi.query.facilities import ErrorHistoryPoint


def get_full_errors_history(
    statsdb: Session,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[ErrorHistoryPoint]:
    """Get a combined error history by merging each facilities histories from the stats database.

    Args:
        statsdb (Session): [description]
        since (Optional[datetime.date], optional): [description]. Defaults to None.
        until (Optional[datetime.date], optional): [description]. Defaults to None.

    Returns:
        list[ErrorHistoryPoint]: [description]
    """
    combined_history: dict[datetime.datetime, int] = {}

    history = statsdb.query(ErrorHistory).filter(
        ErrorHistory.date
        >= (since or (datetime.datetime.utcnow() - datetime.timedelta(days=365)))
    )

    if until:
        history = history.filter(ErrorHistory.date <= until)

    for point in history:
        if point.date not in combined_history:
            combined_history[point.date] = point.count
        else:
            combined_history[point.date] += point.count

    points = [
        ErrorHistoryPoint(time=date, count=count)
        for date, count in combined_history.items()
    ]

    return points

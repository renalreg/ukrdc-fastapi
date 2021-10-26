import datetime
from typing import Optional

from sqlalchemy.orm.session import Session
from ukrdc_sqla.stats import ErrorHistory

from ukrdc_fastapi.query.facilities import HistoryPoint


def get_full_errors_history(
    statsdb: Session,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[HistoryPoint]:
    """Get a combined error history by merging each facilities histories from the stats database.

    Args:
        statsdb (Session): SQLAlchemy session to the stats database.
        since (Optional[datetime.date], optional): Start date. Defaults to last 365 days.
        until (Optional[datetime.date], optional): End date. Defaults to None.

    Returns:
        list[HistoryPoint]: Error history points.
    """
    combined_history: dict[datetime.date, int] = {}

    history = statsdb.query(ErrorHistory).filter(
        ErrorHistory.date
        >= (since or (datetime.datetime.utcnow() - datetime.timedelta(days=365)))
    )

    if until:
        history = history.filter(ErrorHistory.date <= until)

    for point in history:
        if point.count:
            if point.date not in combined_history:
                combined_history[point.date] = point.count
            else:
                combined_history[point.date] += point.count

    points = [
        HistoryPoint(time=date, count=count) for date, count in combined_history.items()
    ]

    return points

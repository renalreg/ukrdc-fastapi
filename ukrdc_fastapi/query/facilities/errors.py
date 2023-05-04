import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.stats import ErrorHistory
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.exceptions import MissingFacilityError
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.utils import daterange


def get_patients_latest_errors(
    ukrdc3: Session,
    errorsdb: Session,
    facility_code: str,
    channels: Optional[list[str]] = None,
) -> Query:
    """Retrieve the most recent error messages for each patient currently receiving errors.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        errorsdb (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        Query: SQLAlchemy query
    """
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    query = (
        errorsdb.query(Message)
        .join(Latest)
        .filter(Latest.facility == facility.code)
        .filter(Message.msg_status == "ERROR")
    )

    # Optionally filter by channels
    if channels is not None:
        query = query.filter(Message.channel_id.in_(channels))

    return query


def get_errors_history(
    ukrdc3: Session,
    statsdb: Session,
    facility_code: str,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[HistoryPoint]:
    """Get a day-by-day error count for a particular facility/unit

    Args:
        ukrdc3 (Session): SQLAlchemy session
        statsdb (Session): SQLAlchemy session
        errorsdb (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        since (Optional[datetime.date]): Filter start date. Defaults to None.
        until (Optional[datetime.date]): Filter end date. Defaults to None.

    Returns:
        list[HistoryPoint]: Time-series error data
    """
    code = (
        ukrdc3.query(Code)
        .filter(Code.coding_standard == "RR1+", Code.code == facility_code)
        .first()
    )

    if not code:
        raise MissingFacilityError(facility_code)

    # Get range
    range_since: datetime.date = since or datetime.date.today() - datetime.timedelta(
        days=365
    )
    range_until: datetime.date = until or datetime.date.today()

    # Get history within range
    history = (
        statsdb.query(ErrorHistory)
        .filter(ErrorHistory.facility == facility_code)
        .filter(ErrorHistory.date >= range_since)
        .filter(ErrorHistory.date <= range_until)
    )

    # Create an initially empty full history dictionary
    full_history: dict[datetime.date, int] = {
        date: 0 for date in daterange(range_since, range_until)
    }

    # For each non-zero history point, add it to the full history
    for history_point in history:
        full_history[history_point.date] = history_point.count or 0

    points = [
        HistoryPoint(time=date, count=count) for date, count in full_history.items()
    ]
    points.sort(key=lambda p: p.time)

    return points

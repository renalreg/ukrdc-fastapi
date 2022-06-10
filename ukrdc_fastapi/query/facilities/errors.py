import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.stats import ErrorHistory, PatientsLatestErrors
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.common import HistoryPoint


def get_patients_latest_errors(
    ukrdc3: Session,
    errorsdb: Session,
    statsdb: Session,
    facility_code: str,
    user: UKRDCUser,
) -> Query:
    """Retrieve the most recent error messages for each patient currently receiving errors.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        errorsdb (Session): SQLAlchemy session
        statsdb (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        Query: SQLAlchemy query
    """
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise HTTPException(404, detail="Facility not found")

    # Assert permissions
    units = Permissions.unit_codes(user.permissions)
    if (Permissions.UNIT_WILDCARD not in units) and (facility.code not in units):
        raise PermissionsError()

    # Get message IDs of patients latest errors
    latest_error_ids = [
        row.id
        for row in (
            statsdb.query(PatientsLatestErrors)
            .filter(PatientsLatestErrors.facility == facility.code)
            .all()
        )
    ]

    return errorsdb.query(Message).filter(Message.id.in_(latest_error_ids))


def get_errors_history(
    ukrdc3: Session,
    statsdb: Session,
    facility_code: str,
    user: UKRDCUser,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[HistoryPoint]:
    """Get a day-by-day error count for a particular facility/unit

    Args:
        ukrdc3 (Session): SQLAlchemy session
        statsdb (Session): SQLAlchemy session
        errorsdb (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user
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
        raise HTTPException(404, detail="Facility not found")

    # Assert permissions
    units = Permissions.unit_codes(user.permissions)
    if (Permissions.UNIT_WILDCARD not in units) and (code.code not in units):
        raise PermissionsError()

    # Get cached statistics
    history = statsdb.query(ErrorHistory).filter(ErrorHistory.facility == facility_code)

    # Default to last year
    history = history.filter(
        ErrorHistory.date
        >= (since or (datetime.datetime.utcnow() - datetime.timedelta(days=365)))
    )

    # Optionally filter by end date
    if until:
        history = history.filter(ErrorHistory.date <= until)

    points = [
        HistoryPoint(time=point.date, count=point.count) for point in history.all()
    ]

    return points

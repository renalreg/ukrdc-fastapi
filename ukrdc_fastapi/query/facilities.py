import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.stats import ErrorHistory, FacilityStats, PatientsLatestErrors
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.facility import FacilitySchema
from ukrdc_fastapi.schemas.message import MessageSchema


class FacilityStatisticsSummarySchema(OrmModel):
    last_updated: Optional[datetime.datetime]

    # Total number of patients we've ever had on record
    total_patients: Optional[int]

    # Total number of patients receiving messages,
    # whether erroring or not
    patients_receiving_messages: Optional[int]

    # Number of patients receiving messages that
    # are most recently succeeding
    patients_receiving_message_success: Optional[int]

    # Number of patients receiving messages that
    # are most recently erroring
    patients_receiving_message_error: Optional[int]


class FacilityStatisticsSchema(FacilityStatisticsSummarySchema):
    # Error message resources for patients receiving
    # messages that are most recently erroring
    patients_latest_errors: list[MessageSchema]


class FacilitySummarySchema(FacilitySchema):
    statistics: FacilityStatisticsSummarySchema


class FacilityDetailsSchema(FacilitySchema):
    statistics: FacilityStatisticsSchema


class ErrorHistoryPoint(OrmModel):
    time: datetime.date
    count: int


# Facility list


def _get_patients_receiving_message_success(stats: FacilityStats):
    if (stats.patients_receiving_messages is None) or (
        stats.patients_receiving_errors is None
    ):
        return None
    return stats.patients_receiving_messages - stats.patients_receiving_errors


def get_facilities(
    ukrdc3: Session, statsdb: Session, user: UKRDCUser, include_empty: bool = False
) -> list[FacilitySummarySchema]:
    """Get a list of all unit/facility summaries available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        statsdb (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilitySummarySchema]: List of units/facilities
    """

    codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+")

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        codes = codes.filter(Code.code.in_(units))
    facility_codes = codes.all()

    # Create a list to store our response
    facility_list: list[FacilitySummarySchema] = []

    # Fetch stats for facilities we're listing
    facility_stats_dict = {
        row.facility: row
        for row in statsdb.query(FacilityStats)
        .filter(FacilityStats.facility.in_([code.code for code in facility_codes]))
        .all()
    }

    for code in facility_codes:
        stats = facility_stats_dict.get(code.code)
        if stats and (
            include_empty  # Always include all facilities if requested
            or (stats.total_patients or 0) > 0  # Include facilities with patients
        ):
            facility_list.append(
                FacilitySummarySchema(
                    id=code.code,
                    description=code.description,
                    statistics=FacilityStatisticsSummarySchema(
                        last_updated=stats.last_updated,
                        total_patients=stats.total_patients,
                        patients_receiving_messages=stats.patients_receiving_messages,
                        patients_receiving_message_success=_get_patients_receiving_message_success(
                            stats
                        ),
                        patients_receiving_message_error=stats.patients_receiving_errors,
                    ),
                )
            )

    return facility_list


# Facility error statistics


def _expand_cached_facility_statistics(
    facility_code: str, errorsdb: Session, statsdb: Session
) -> FacilityStatisticsSchema:
    stats = (
        statsdb.query(FacilityStats)
        .filter(FacilityStats.facility == facility_code)
        .first()
    )
    latest_error_ids = [
        row.id
        for row in (
            statsdb.query(PatientsLatestErrors)
            .filter(PatientsLatestErrors.facility == facility_code)
            .all()
        )
    ]

    return FacilityStatisticsSchema(
        last_updated=stats.last_updated,
        total_patients=stats.total_patients,
        patients_receiving_messages=stats.patients_receiving_messages,
        patients_receiving_message_success=_get_patients_receiving_message_success(
            stats
        ),
        patients_receiving_message_error=stats.patients_receiving_errors,
        # Build an array of Message objects from the cached message IDs
        patients_latest_errors=[
            MessageSchema.from_orm(m)
            for m in errorsdb.query(Message)
            .filter(Message.id.in_(latest_error_ids))
            .order_by(Message.received.desc())
        ],
    )


def get_facility(
    ukrdc3: Session,
    errorsdb: Session,
    statsdb: Session,
    facility_code: str,
    user: UKRDCUser,
) -> FacilityDetailsSchema:
    """Get a summary of a particular facility/unit

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        FacilityDetailsSchema: Matched facility
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
    return FacilityDetailsSchema(
        id=code.code,
        description=code.description,
        statistics=_expand_cached_facility_statistics(code.code, errorsdb, statsdb),
    )


# Facility error history


def get_errors_history(
    ukrdc3: Session,
    statsdb: Session,
    facility_code: str,
    user: UKRDCUser,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
) -> list[ErrorHistoryPoint]:
    """Get a day-by-day error count for a particular facility/unit

    Args:
        ukrdc3 (Session): SQLAlchemy session
        errorsdb (Session): SQLAlchemy session
        redis (Redis): Redis session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user
        since (Optional[datetime.date]): Filter start date. Defaults to None.
        until (Optional[datetime.date]): Filter end date. Defaults to None.

    Returns:
        list[ErrorHistoryPoint]: Time-series error data
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

    if since:
        history = history.filter(ErrorHistory.date >= since)
    if until:
        history = history.filter(ErrorHistory.date <= until)

    points = [
        ErrorHistoryPoint(
            time=point.date,
            count=point.count,
        )
        for point in history.all()
    ]

    return points

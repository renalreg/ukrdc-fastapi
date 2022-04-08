import datetime
from typing import Optional, Tuple

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.stats import (
    ErrorHistory,
    FacilityLatestMessages,
    FacilityStats,
    PatientsLatestErrors,
)
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.schemas.facility import FacilitySchema


class FacilityDataFlowSchema(OrmModel):
    pkb_in: bool
    pkb_out: bool
    pkb_message_exclusions: list[str]


class FacilityStatisticsSchema(OrmModel):
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


class FacilityLatestMessageSchema(OrmModel):
    last_updated: Optional[datetime.datetime]

    # Date of the most recent message received for the facility
    last_message_received_at: Optional[datetime.datetime]


class FacilityDetailsSchema(FacilitySchema):
    latest_message: FacilityLatestMessageSchema
    statistics: FacilityStatisticsSchema
    data_flow: FacilityDataFlowSchema


# Convenience functions


def _get_patients_receiving_message_success(stats: FacilityStats):
    if (stats.patients_receiving_messages is None) or (
        stats.patients_receiving_errors is None
    ):
        return None
    return stats.patients_receiving_messages - stats.patients_receiving_errors


def _expand_facility_statistics(
    stats: Optional[FacilityStats],
) -> FacilityStatisticsSchema:
    return FacilityStatisticsSchema(
        last_updated=(stats.last_updated if stats else None),
        total_patients=(stats.total_patients if stats else None),
        patients_receiving_messages=(
            stats.patients_receiving_messages if stats else None
        ),
        patients_receiving_message_success=(
            _get_patients_receiving_message_success(stats) if stats else None
        ),
        patients_receiving_message_error=(
            stats.patients_receiving_errors if stats else None
        ),
    )


def _expand_latest_messages(latest_messages: Optional[FacilityLatestMessages]):
    return FacilityLatestMessageSchema(
        last_updated=latest_messages.last_updated if latest_messages else None,
        last_message_received_at=latest_messages.last_message_received_at
        if latest_messages
        else None,
    )


# Facility list


def get_facilities(
    ukrdc3: Session, statsdb: Session, user: UKRDCUser, include_inactive: bool = False
) -> list[FacilityDetailsSchema]:
    """Get a list of all unit/facility summaries available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        statsdb (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilityDetailsSchema]: List of units/facilities
    """
    # TODO: This badly needs optimization and cleanup. This whole submodule could do with some TLC

    facilities = ukrdc3.query(Facility)

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        facilities = facilities.filter(Facility.code.in_(units))

    # Execute statement to retreive available facilities list for this user
    available_facilities = facilities.all()

    # Create a list to store our response
    facility_list: list[FacilityDetailsSchema] = []

    facility_stats_dict: dict[str, Tuple[FacilityStats, FacilityLatestMessages]] = {
        row[0].facility: row
        for row in (
            statsdb.query(FacilityStats, FacilityLatestMessages)
            .filter(
                FacilityStats.facility.in_(
                    [facility.code for facility in available_facilities]
                )
            )
            .outerjoin(
                FacilityLatestMessages,
                FacilityLatestMessages.facility == FacilityStats.facility,
            )
            .all()
        )
    }

    for facility in available_facilities:
        # Find the stats for this specific facility
        stats, latest_messages = facility_stats_dict.get(facility.code, (None, None))
        # If stats exist, expand them and add this facility to the response

        # Always include all facilities if include_inactive==True
        # Otherwise, only include facilities with active incoming files
        if include_inactive or (
            latest_messages and latest_messages.last_message_received_at
        ):
            facility_list.append(
                FacilityDetailsSchema(
                    id=facility.code,
                    description=facility.description,
                    latest_message=_expand_latest_messages(latest_messages),
                    statistics=_expand_facility_statistics(stats),
                    data_flow=FacilityDataFlowSchema(
                        pkb_in=facility.pkb_in,
                        pkb_out=facility.pkb_out,
                        pkb_message_exclusions=facility.pkb_msg_exclusions or [],
                    ),
                )
            )

    return facility_list


# Facility error statistics


def get_facility(
    ukrdc3: Session,
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
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise HTTPException(404, detail="Facility not found")

    # Assert permissions
    units = Permissions.unit_codes(user.permissions)
    if (Permissions.UNIT_WILDCARD not in units) and (facility.code not in units):
        raise PermissionsError()

    # Get cached statistics
    stats, latest_messages = (
        statsdb.query(FacilityStats, FacilityLatestMessages)
        .filter(FacilityStats.facility == facility_code)
        .outerjoin(
            FacilityLatestMessages,
            FacilityLatestMessages.facility == FacilityStats.facility,
        )
        .first()
    )

    return FacilityDetailsSchema(
        id=facility.code,
        description=facility.description,
        latest_message=_expand_latest_messages(latest_messages),
        statistics=_expand_facility_statistics(stats),
        data_flow=FacilityDataFlowSchema(
            pkb_in=facility.pkb_in,
            pkb_out=facility.pkb_out,
            pkb_message_exclusions=facility.pkb_msg_exclusions or [],
        ),
    )


# Facility sub resources


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

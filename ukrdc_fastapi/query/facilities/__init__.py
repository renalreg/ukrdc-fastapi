import datetime
from typing import Optional, Tuple

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.stats import FacilityLatestMessages, FacilityStats
from ukrdc_sqla.ukrdc import Code, Facility

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.base import OrmModel
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


# Security functions


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.filter(Facility.code.in_(units))


def _assert_permission(facility: Facility, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if (Permissions.UNIT_WILDCARD not in units) and (facility.code not in units):
        raise PermissionsError()


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
    ukrdc3: Session,
    statsdb: Session,
    user: UKRDCUser,
    include_inactive: bool = False,
    include_empty: bool = False,
) -> list[FacilityDetailsSchema]:
    """Get a list of all unit/facility summaries available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        statsdb (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilityDetailsSchema]: List of units/facilities
    """
    # TODO: This badly needs optimization and cleanup. Need a profiler to profile the final comprehension

    facilities = ukrdc3.query(Facility)

    # Filter results by unit permissions
    facilities = _apply_query_permissions(facilities, user)

    # Execute statement to retreive available facilities list for this user
    available_facilities = facilities.all()

    # Pre-fetch descriptions for all facilities available to the user
    # We want to avoid using facility.description as this is an associationproxy,
    # meaning that a new query is generated for each access, in this case for each
    # facility in the list. We speed this up by orders of magnitude by fetching ALL
    # descriptions in one query.
    descriptions = {
        code.code: code.description
        for code in ukrdc3.query(Code)
        .filter(Code.coding_standard == "RR1+")
        .filter(Code.code.in_([facility.code for facility in available_facilities]))
    }

    # Get all stats from all tables for all facilities available to the user
    stats_query = (
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
    )

    # Execute the stats query and store in a facility-code-keyed dictionary
    facility_stats_dict: dict[str, Tuple[FacilityStats, FacilityLatestMessages]] = {
        row[0].facility: row for row in stats_query
    }

    facility_list: list[FacilityDetailsSchema] = []

    for facility in available_facilities:
        # Find pre-fetched stats for this facility
        stats, latests = facility_stats_dict.get(facility.code, (None, None))
        # Find pre-fetched description for this facility
        description = descriptions.get(facility.code, None)

        # Should this facility be included in the list?
        include_this_facility = (
            include_inactive or (latests and latests.last_message_received_at)
        ) and (include_empty or (stats and (stats.total_patients or 0) > 0))

        if include_this_facility:
            facility_list.append(
                FacilityDetailsSchema(
                    id=facility.code,
                    description=description,
                    data_flow=FacilityDataFlowSchema(
                        pkb_in=facility.pkb_in,
                        pkb_out=facility.pkb_out,
                        pkb_message_exclusions=facility.pkb_msg_exclusions or [],
                    ),
                    latest_message=_expand_latest_messages(latests),
                    statistics=_expand_facility_statistics(stats),
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
    _assert_permission(facility, user)

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

from typing import Optional

from redis import Redis
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.ukrdc import Code, Facility, PatientRecord

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import MissingFacilityError
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.facility import (
    FacilityDataFlowSchema,
    FacilityDetailsSchema,
    FacilityExtractsSchema,
    FacilityStatisticsSchema,
)
from ukrdc_fastapi.utils.cache import BasicCache, CacheKey
from ukrdc_fastapi.utils.records import ABSTRACT_FACILITIES

# Facility with error statistics


def get_facility(
    ukrdc3: Session,
    errorsdb: Session,
    facility_code: str,
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
        raise MissingFacilityError(facility_code)

    # Get facility messages
    messages = (
        errorsdb.query(Latest)
        .join(Message)
        .filter(Latest.facility == facility.code)
        .order_by(Message.received.desc())
    )

    latest_message = messages.first()
    patients_receiving_messages = messages.count()
    patients_receiving_errors = messages.filter(Message.msg_status == "ERROR").count()

    total_records = (
        ukrdc3.query(PatientRecord)
        .filter(PatientRecord.sendingfacility == facility_code)
        .filter(PatientRecord.sendingextract.notin_(["PVMIG", "HSMIG"]))
        .count()
    )

    statistics = FacilityStatisticsSchema(
        total_patients=total_records,
        patients_receiving_messages=patients_receiving_messages,
        patients_receiving_message_error=patients_receiving_errors,
        patients_receiving_message_success=(
            patients_receiving_messages - patients_receiving_errors
        ),
    )

    return FacilityDetailsSchema(
        id=facility.code,
        description=facility.description,
        last_message_received_at=latest_message.message.received
        if latest_message
        else None,
        statistics=statistics,
        data_flow=FacilityDataFlowSchema(
            pkb_in=facility.pkb_in,
            pkb_out=facility.pkb_out,
            pkb_message_exclusions=facility.pkb_msg_exclusions or [],
        ),
    )


# Facility extract statistics


def get_facility_extracts(
    ukrdc3: Session,
    facility_code: str,
) -> FacilityExtractsSchema:
    """Get extract counts for a particular facility/unit

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code
        user (UKRDCUser): Logged-in user

    Returns:
        FacilityExtractsSchema: Extract counts
    """
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    query = (
        ukrdc3.query(PatientRecord.sendingextract, func.count("*"))
        .filter(PatientRecord.sendingfacility == facility_code)
        .group_by(PatientRecord.sendingextract)
    )

    extracts = dict(query.all())

    return FacilityExtractsSchema(
        ukrdc=extracts.get("UKRDC", 0),
        pv=extracts.get("PV", 0),
        radar=extracts.get("RADAR", 0),
        survey=extracts.get("SURVEY", 0),
        pvmig=extracts.get("PVMIG", 0),
        hsmig=extracts.get("HSMIG", 0),
        ukrr=extracts.get("UKRR", 0),
    )


# Facility list


def build_facilities_list(
    facilities_query: Query, ukrdc3: Session, errorsdb: Session
) -> list[FacilityDetailsSchema]:
    """Build a list of FacilityDetailsSchema objects from a facilities query.

    Args:
        facilities_query (Query): _description_
        ukrdc3 (Session): _description_
        errorsdb (Session): _description_

    Returns:
        list[FacilityDetailsSchema]: _description_
    """

    # Execute statement to retreive available facilities list for this user
    available_facilities = facilities_query.all()

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

    # Build statistics
    total_records_q = (
        ukrdc3.query(PatientRecord.sendingfacility, func.count("*"))
        .filter(PatientRecord.sendingextract.notin_(["PVMIG", "HSMIG"]))
        .filter(
            PatientRecord.sendingfacility.in_(
                [facility.code for facility in available_facilities]
            )
        )
        .group_by(PatientRecord.sendingfacility)
    )
    total_records_dict = {row[0].upper(): row[1] for row in total_records_q}

    # Get a count of each facility-status combination from latest messages
    # We can use these counts to build up all "current status" statistics,
    # e.g. number of patients most recently receiving error messages
    status_counts_query = (
        errorsdb.query(
            Latest.facility, Message.msg_status, func.count(Message.msg_status)
        )
        .join(Message)
        .filter(
            Latest.facility.in_([facility.code for facility in available_facilities])
        )
        .group_by(Latest.facility, Message.msg_status)
    )
    # Create an empty dict to store facility status counts
    status_counts_dict: dict[str, dict[str, int]] = {}
    # Iterate over each row in the query result
    for row in status_counts_query:
        # Set dict[facility][status] = count
        status_counts_dict.setdefault(row[0].upper(), {})[row[1]] = row[2]

    # Get the most recent message received time for each facility
    most_recent_q = (
        errorsdb.query(Latest.facility, func.max(Message.received))
        .join(Message)
        .filter(
            Latest.facility.in_([facility.code for facility in available_facilities])
        )
        .group_by(Latest.facility)
    )
    most_recent_dict = {row[0].upper(): row[1] for row in most_recent_q}

    # Build list of facility details
    facility_list: list[FacilityDetailsSchema] = []
    for facility in available_facilities:
        # Find pre-fetched total records count for this facility
        total_records = total_records_dict.get(facility.code.upper(), 0)
        # Find pre-fetched most recent message received time for this facility
        last_message_received_at = most_recent_dict.get(facility.code.upper())

        # Find pre-fetched description for this facility
        description: Optional[str] = descriptions.get(facility.code.upper())

        # Find pre-fetched status counts for this facility
        status_stats: dict[str, int] = status_counts_dict.get(facility.code.upper(), {})
        patients_receiving_errors = status_stats.get("ERROR", 0)
        patients_receiving_messages = sum(status_stats.values())

        facility_list.append(
            FacilityDetailsSchema(
                id=facility.code,
                description=description,
                last_message_received_at=last_message_received_at,
                data_flow=FacilityDataFlowSchema(
                    pkb_in=facility.pkb_in,
                    pkb_out=facility.pkb_out,
                    pkb_message_exclusions=facility.pkb_msg_exclusions or [],
                ),
                statistics=FacilityStatisticsSchema(
                    total_patients=total_records,
                    patients_receiving_messages=patients_receiving_messages,
                    patients_receiving_message_error=patients_receiving_errors,
                    patients_receiving_message_success=(
                        patients_receiving_messages - patients_receiving_errors
                    ),
                ),
            )
        )

    return facility_list


def get_facilities(
    ukrdc3: Session,
    errorsdb: Session,
    redis: Redis,
    include_inactive: bool = False,
    include_empty: bool = False,
) -> list[FacilityDetailsSchema]:
    """Get a list of all unit/facility summaries available to the current user.

    Args:
        ukrdc3 (Session): SQLALchemy session
        statsdb (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilityDetailsSchema]: List of units/facilities
    """

    # Look for a pre-calculated cache of the facilities list (see `ukrdc_fastapi.tasks.repeated`)
    cache = BasicCache(redis, CacheKey.FACILITIES_LIST)
    if not cache.exists:
        cache.set(
            build_facilities_list(
                ukrdc3.query(Facility).filter(
                    Facility.code.notin_(ABSTRACT_FACILITIES)
                ),
                ukrdc3,
                errorsdb,
            ),
            expire=settings.cache_facilities_list_seconds,
        )

    facilities = [FacilityDetailsSchema(**facility) for facility in cache.get()]

    # Filter out inactive facilities by checking for last_message_received_at
    if not include_inactive:
        facilities = [
            facility for facility in facilities if facility.last_message_received_at
        ]

    # Filter out empty facilities by checking for total_records existing and > 0
    if not include_empty:
        facilities = [
            facility
            for facility in facilities
            if (facility.statistics.total_patients or 0) > 0
        ]

    return facilities

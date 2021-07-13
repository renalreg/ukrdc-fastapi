import datetime
import json
from typing import Optional

from fastapi.exceptions import HTTPException
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import Code, PatientRecord

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.errors import get_errors
from ukrdc_fastapi.query.patientrecords import get_patientrecords
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.facility import FacilitySchema
from ukrdc_fastapi.utils.statistics import TotalDayPrev, total_day_prev


class FacilityStatisticsSchema(OrmModel):
    records_with_errors: int
    patient_records: TotalDayPrev
    errors: TotalDayPrev


class FacilityDetailsSchema(FacilitySchema):
    statistics: FacilityStatisticsSchema


def _get_error_stats(
    errorsdb: Session,
    user: UKRDCUser,
    facility: Optional[str] = None,
) -> TotalDayPrev:
    """Get total, today, and yesterday error message counts for a facility.
    Total gives the total messages from all time (since 1/1/1970), not just last year.

    Args:
        errorsdb (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        facility (Optional[str], optional): Facility code to filter by. Defaults to None.

    Returns:
        TotalDayPrev: Error statistics
    """
    errors_query = get_errors(
        errorsdb,
        user,
        facility=facility,
        since=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )
    return total_day_prev(errors_query, Message, "received")


def _get_error_ni_count(
    errorsdb: Session,
    user: UKRDCUser,
    facility: Optional[str] = None,
) -> int:
    """Get the number of unique national identifiers appearing in the errorsdb for a facility

    Args:
        errorsdb (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        facility (Optional[str], optional): Facility code to filter by. Defaults to None.

    Returns:
        int: Number of unique NIs with error messages
    """
    errors_query = get_errors(
        errorsdb,
        user,
        facility=facility,
        since=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )
    errors_set = errors_query.distinct(Message.ni)
    return errors_set.count()


def _get_record_stats(
    ukrdc3: Session, user: UKRDCUser, facility: Optional[str] = None
) -> TotalDayPrev:
    """Get total, today, and yesterday PatientRecord counts for a facility.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        facility (Optional[str], optional): Facility code to filter by. Defaults to None.

    Returns:
        TotalDayPrev: PatientRecord statistics
    """
    query = get_patientrecords(ukrdc3, user).filter(
        PatientRecord.sendingfacility == facility
    )
    return total_day_prev(query, PatientRecord, "creation_date")


def _get_and_cache_facility(
    code: Code,
    ukrdc3: Session,
    errorsdb: Session,
    redis: Redis,
) -> FacilityDetailsSchema:
    """
    Retrieve, or generate and cache, facility statistics.
    Data is retreieved as the internal superuser to ensure all requests
    end up with the same counts. Permissions are handled downstream, in
    `get_facility(...)`
    """
    # Check for cached statistics
    redis_key: str = f"ukrdc3:facilities:{code.code}:statistics"
    if not redis.exists(redis_key):
        statistics = FacilityStatisticsSchema(
            records_with_errors=_get_error_ni_count(
                errorsdb, auth.superuser, facility=code.code
            ),
            patient_records=_get_record_stats(
                ukrdc3, auth.superuser, facility=code.code
            ),
            errors=_get_error_stats(errorsdb, auth.superuser, facility=code.code),
        )
        redis.set(redis_key, statistics.json())  # type: ignore
        redis.expire(redis_key, settings.cache_statistics_seconds)
    else:
        statistics_json: str = redis.get(redis_key)  # type: ignore
        statistics = FacilityStatisticsSchema.parse_raw(statistics_json)

    facility_details = FacilityDetailsSchema(
        id=code.code,
        description=code.description,
        statistics=statistics,
    )

    return facility_details


def get_facilities(
    ukrdc3: Session, redis: Redis, user: UKRDCUser
) -> list[FacilitySchema]:
    """Get a list of all unit/facility codes available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        redis (Redis): Redis session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilitySchema]: List of unit codes
    """
    redis_key: str = "ukrdc3:facilities"

    if not redis.exists(redis_key):
        codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+")
        facilities = [
            FacilitySchema(id=code.code, description=code.description) for code in codes
        ]
        redis.set(redis_key, json.dumps([facility.dict() for facility in facilities]))
        # Cache for 12 hours
        redis.expire(redis_key, 43200)

    else:
        facilities_json: Optional[str] = redis.get(redis_key)
        if not facilities_json:
            facilities = []
        else:
            facilities = [
                FacilitySchema(**facility) for facility in json.loads(facilities_json)
            ]

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        facilities = [facility for facility in facilities if facility.id in units]

    return facilities


def get_facility(
    ukrdc3: Session,
    errorsdb: Session,
    redis: Redis,
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
    return _get_and_cache_facility(code, ukrdc3, errorsdb, redis)

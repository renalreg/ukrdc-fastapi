import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from redis import Redis
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import Code, PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.facility import FacilityMessageSummarySchema, FacilitySchema


class FacilityStatisticsSchema(OrmModel):
    patient_records: Optional[int]
    messages: FacilityMessageSummarySchema
    last_updated: Optional[datetime.datetime]


class FacilityDetailsSchema(FacilitySchema):
    statistics: FacilityStatisticsSchema


class ErrorHistoryPoint(OrmModel):
    time: datetime.date
    count: int


class ErrorHistory(OrmModel):
    __root__: list[ErrorHistoryPoint]


# Facility list


def get_facilities(ukrdc3: Session, user: UKRDCUser) -> list[FacilitySchema]:
    """Get a list of all unit/facility codes available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        redis (Redis): Redis session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilitySchema]: List of unit codes
    """

    codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+")

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        codes = codes.filter(Code.code.in_(units))

    return [
        FacilitySchema(id=code.code, description=code.description)
        for code in codes.all()
    ]


# Facility error statistics


def _get_message_sumary(
    errorsdb: Session,
    facility: Optional[str] = None,
) -> FacilityMessageSummarySchema:
    """
    Generate a summary of message success and errors for a facility.
    """
    query = (
        errorsdb.query(Message)
        .filter(Message.facility == facility)
        .filter(Message.ni.isnot(None))
        .order_by(Message.ni, Message.received.desc())
        .distinct(Message.ni)
    )

    all_nis = query.all()
    error_nis_messages = [m for m in all_nis if m.ni and m.msg_status == "ERROR"]

    print(f"Done caching {facility}")

    return FacilityMessageSummarySchema(
        total_IDs_count=len(all_nis),
        success_IDs_count=len(all_nis) - len(error_nis_messages),
        error_IDs_count=len(error_nis_messages),
        error_IDs_messages=error_nis_messages,
    )


def cache_facility_statistics(
    code: Code,
    ukrdc3: Session,
    errorsdb: Session,
    redis: Redis,
) -> FacilityDetailsSchema:
    """
    Generate and cache facility statistics. Only ever called as a background task.
    """
    redis_key: str = f"ukrdc3:facilities:{code.code}:statistics"

    statistics_dict = {
        "patient_records": ukrdc3.query(PatientRecord)
        .filter(PatientRecord.sendingfacility == code.code)
        .count(),
        "messages": _get_message_sumary(errorsdb, code.code),
        "last_updated": datetime.datetime.now(),
    }
    statistics = FacilityStatisticsSchema(**statistics_dict)
    redis.set(redis_key, statistics.json())  # type: ignore

    facility_details = FacilityDetailsSchema(
        id=code.code,
        description=code.description,
        statistics=statistics,
    )

    return facility_details


def _get_cached_facility_details(code: Code, redis: Redis) -> FacilityDetailsSchema:
    """
    Retrieve cached facility statistics, if they exist.
    """
    # Check for cached statistics
    redis_key: str = f"ukrdc3:facilities:{code.code}:statistics"
    if not redis.exists(redis_key):
        statistics = FacilityStatisticsSchema(
            patient_records=None,
            messages=FacilityMessageSummarySchema.empty(),
            last_updated=None,
        )
    else:
        statistics_json: str = redis.get(redis_key)  # type: ignore
        statistics = FacilityStatisticsSchema.parse_raw(statistics_json)

    facility_details = FacilityDetailsSchema(
        id=code.code,
        description=code.description,
        statistics=statistics,
    )

    return facility_details


def get_facility(
    ukrdc3: Session,
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
    return _get_cached_facility_details(code, redis)


# Facility error history


def cache_facility_error_history(
    code: Code, errorsdb: Session, redis: Redis
) -> ErrorHistory:
    """
    Generate and cache facility error history. Only ever called as a background task.
    """
    redis_key: str = f"ukrdc3:facilities:{code.code}:errorhistory"

    trunc_func = func.date_trunc("day", Message.received)
    query = (
        errorsdb.query(
            trunc_func,
            Message.facility,
            Message.msg_status,
            func.count(Message.received),
        )
        .filter(Message.facility == code.code)
        .filter(Message.msg_status == "ERROR")
        .filter(trunc_func >= datetime.datetime.utcnow() - datetime.timedelta(days=365))
    )
    query = query.group_by(trunc_func, Message.facility, Message.msg_status)

    counts: ErrorHistory = ErrorHistory(
        __root__=[ErrorHistoryPoint(time=item[0], count=item[-1]) for item in query]
    )
    counts_json = counts.json()
    redis.set(redis_key, counts_json)  # type: ignore

    return counts


def _get_cached_facility_error_history(code: Code, redis: Redis) -> ErrorHistory:
    # Check for cached statistics
    redis_key: str = f"ukrdc3:facilities:{code.code}:errorhistory"
    if redis.exists(redis_key):
        counts_json: str = redis.get(redis_key)  # type: ignore
        return ErrorHistory.parse_raw(counts_json)
    return ErrorHistory.parse_obj([])


def get_errors_history(
    ukrdc3: Session,
    redis: Redis,
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
    history = _get_cached_facility_error_history(code, redis).__root__

    if since:
        history = [point for point in history if point.time >= since]
    if until:
        history = [point for point in history if point.time <= until]

    return history

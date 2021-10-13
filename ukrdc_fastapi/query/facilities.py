import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from pydantic.main import BaseModel
from redis import Redis
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import Code, PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.facility import FacilitySchema
from ukrdc_fastapi.schemas.message import MessageSchema


class CachedFacilityMessageSummarySchema(BaseModel):
    error_nis_message_ids: list[int]
    all_nis: int


class CachedFacilityStatisticsSchema(BaseModel):
    patient_records: Optional[int]
    messages: CachedFacilityMessageSummarySchema
    last_updated: Optional[datetime.datetime]


class FacilityMessageSummarySchema(OrmModel):
    total_IDs_count: Optional[int] = None
    success_IDs_count: Optional[int] = None
    error_IDs_count: Optional[int] = None

    error_IDs_messages: Optional[list[MessageSchema]] = None

    @classmethod
    def empty(cls):
        """
        Build an empty FacilityMessageSummarySchema object
        """
        return cls(
            total_IDs_count=None,
            success_IDs_count=None,
            error_IDs_count=None,
            error_IDs=None,
        )


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
) -> CachedFacilityMessageSummarySchema:
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
    error_nis_message_ids = [m.id for m in all_nis if m.ni and m.msg_status == "ERROR"]

    return CachedFacilityMessageSummarySchema(
        error_nis_message_ids=error_nis_message_ids,
        all_nis=len(all_nis),
    )


def cache_facility_statistics(
    code: Code, ukrdc3: Session, errorsdb: Session, redis: Redis
) -> None:
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
    statistics = CachedFacilityStatisticsSchema(**statistics_dict)
    redis.set(redis_key, statistics.json())  # type: ignore


def _expand_cached_facility_statistics(
    code: Code, errorsdb: Session, redis: Redis
) -> FacilityStatisticsSchema:
    redis_key: str = f"ukrdc3:facilities:{code.code}:statistics"
    # Return empty stats if no cached data is found
    if not redis.exists(redis_key):
        return FacilityStatisticsSchema(
            patient_records=None,
            messages=FacilityMessageSummarySchema.empty(),
            last_updated=None,
        )

    cached_statistics_json: str = redis.get(redis_key)  # type: ignore
    cached_statistics = CachedFacilityStatisticsSchema.parse_raw(cached_statistics_json)

    return FacilityStatisticsSchema(
        patient_records=cached_statistics.patient_records,
        messages=FacilityMessageSummarySchema(
            total_IDs_count=cached_statistics.messages.all_nis,
            success_IDs_count=cached_statistics.messages.all_nis
            - len(cached_statistics.messages.error_nis_message_ids),
            error_IDs_count=len(cached_statistics.messages.error_nis_message_ids),
            # Build an array of Message objects from the cached message IDs
            error_IDs_messages=[
                MessageSchema.from_orm(m)
                for m in errorsdb.query(Message)
                .filter(
                    Message.id.in_(cached_statistics.messages.error_nis_message_ids)
                )
                .order_by(Message.received.desc())
            ],
        ),
        last_updated=cached_statistics.last_updated,
    )


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
    return FacilityDetailsSchema(
        id=code.code,
        description=code.description,
        statistics=_expand_cached_facility_statistics(code, errorsdb, redis),
    )


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
        .filter(Message.msg_status.in_(["ERROR", "RESOLVED"]))
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

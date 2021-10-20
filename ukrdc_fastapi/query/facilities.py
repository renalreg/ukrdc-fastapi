import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
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


class CachedFacilityStatisticsSchema(BaseModel):
    last_updated: Optional[datetime.datetime]
    total_patients: Optional[int]

    # List of IDs of messages that are the
    # most recent message for a patient AND are an error
    patients_latest_errors: list[int]

    # Total number of patients receiving messages,
    # whether erroring or not
    patients_receiving_messages: Optional[int]

    @classmethod
    def empty(cls):
        return cls(
            last_updated=None,
            total_patients=None,
            patients_latest_errors=[],
            patients_receiving_messages=None,
        )


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


class ErrorHistory(OrmModel):
    __root__: list[ErrorHistoryPoint]


# Facility list


def get_facilities(
    ukrdc3: Session, redis: Redis, user: UKRDCUser, include_empty: bool = False
) -> list[FacilitySummarySchema]:
    """Get a list of all unit/facility summaries available to the current user

    Args:
        ukrdc3 (Session): SQLALchemy session
        redis (Redis): Redis session
        user (UKRDCUser): Logged-in user object

    Returns:
        list[FacilitySummarySchema]: List of units/facilities
    """

    codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+")

    # Filter results by unit permissions
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD not in units:
        codes = codes.filter(Code.code.in_(units))

    facility_list: list[FacilitySummarySchema] = []

    for code in codes.all():
        cached_statistics = _get_cached_facility_statistics(code.code, redis)
        if (
            include_empty
            or (cached_statistics.total_patients or 0) > 0
            or cached_statistics.total_patients is None
        ):
            facility_list.append(
                FacilitySummarySchema(
                    id=code.code,
                    description=code.description,
                    # TODO: Remove duplicate code here and _expand_cached_facility_statistics
                    statistics=FacilityStatisticsSummarySchema(
                        last_updated=cached_statistics.last_updated,
                        total_patients=cached_statistics.total_patients,
                        patients_receiving_messages=cached_statistics.patients_receiving_messages,
                        patients_receiving_message_success=(
                            cached_statistics.patients_receiving_messages
                            - len(cached_statistics.patients_latest_errors)
                            if cached_statistics.last_updated
                            else None
                        ),
                        patients_receiving_message_error=len(
                            cached_statistics.patients_latest_errors
                        ),
                    ),
                )
            )

    return facility_list


# Facility error statistics


def cache_facility_statistics(
    code: Code, ukrdc3: Session, errorsdb: Session, redis: Redis
) -> None:
    """
    Generate and cache facility statistics. Only ever called as a background task.
    """
    redis_key: str = f"ukrdc3:facilities:{code.code}:statistics"

    query = (
        errorsdb.query(Message)
        .filter(Message.facility == code.code)
        .filter(Message.ni.isnot(None))
        .filter(Message.filename.isnot(None))
        .order_by(Message.ni, Message.received.desc())
        .distinct(Message.ni)
    )

    patients_latest_messages = query.all()
    patients_latest_errors = [
        m.id for m in patients_latest_messages if m.ni and m.msg_status == "ERROR"
    ]

    statistics = CachedFacilityStatisticsSchema(
        last_updated=datetime.datetime.now(),
        total_patients=ukrdc3.query(
            PatientRecord.sendingfacility, PatientRecord.ukrdcid
        )
        .filter(PatientRecord.sendingfacility == code.code)
        .distinct()
        .count(),
        patients_latest_errors=patients_latest_errors,
        patients_receiving_messages=len(patients_latest_messages),
    )
    redis.set(redis_key, statistics.json())  # type: ignore


def _get_cached_facility_statistics(
    facility_code: str, redis: Redis
) -> CachedFacilityStatisticsSchema:
    redis_key: str = f"ukrdc3:facilities:{facility_code}:statistics"
    # Return empty stats if no cached data is found
    if not redis.exists(redis_key):
        return CachedFacilityStatisticsSchema.empty()

    cached_statistics_json: str = redis.get(redis_key)  # type: ignore
    return CachedFacilityStatisticsSchema.parse_raw(cached_statistics_json)


def _expand_cached_facility_statistics(
    facility_code: str, errorsdb: Session, redis: Redis
) -> FacilityStatisticsSchema:
    cached_statistics = _get_cached_facility_statistics(facility_code, redis)

    return FacilityStatisticsSchema(
        last_updated=cached_statistics.last_updated,
        total_patients=cached_statistics.total_patients,
        patients_receiving_messages=cached_statistics.patients_receiving_messages,
        patients_receiving_message_success=(
            cached_statistics.patients_receiving_messages
            - len(cached_statistics.patients_latest_errors)
            if cached_statistics.patients_receiving_messages
            else None
        ),
        patients_receiving_message_error=len(cached_statistics.patients_latest_errors),
        # Build an array of Message objects from the cached message IDs
        patients_latest_errors=[
            MessageSchema.from_orm(m)
            for m in errorsdb.query(Message)
            .filter(Message.id.in_(cached_statistics.patients_latest_errors))
            .order_by(Message.received.desc())
        ],
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
        statistics=_expand_cached_facility_statistics(code.code, errorsdb, redis),
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


def _get_cached_facility_error_history(
    facility_code: str, redis: Redis
) -> ErrorHistory:
    # Check for cached statistics
    redis_key: str = f"ukrdc3:facilities:{facility_code}:errorhistory"
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
    history = _get_cached_facility_error_history(code.code, redis).__root__

    if since:
        history = [point for point in history if point.time >= since]
    if until:
        history = [point for point in history if point.time <= until]

    return history

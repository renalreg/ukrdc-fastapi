import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.errors import ExtendedErrorSchema, make_extended_error


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.filter(Message.facility.in_(units))


def _assert_permission(message: Message, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if message.facility not in units:
        raise PermissionsError()


def get_errors(
    errorsdb: Session,
    user: UKRDCUser,
    status: str = "ERROR",
    nis: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sort_query: bool = True,
) -> Query:
    """Get a list of error messages from the errorsdb

    Args:
        errorsdb (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        status (str, optional): Status code to filter by. Defaults to "ERROR".
        nis (Optional[list[str]], optional): List of pateint NIs to filer by. Defaults to None.
        facility (Optional[str], optional): Unit/facility code to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show records since datetime. Defaults to 365 days ago.
        until (Optional[datetime.datetime], optional): Show records until datetime. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    query = errorsdb.query(Message)

    # Default to showing last 365 days
    since_datetime: datetime.datetime = (
        since or datetime.datetime.utcnow() - datetime.timedelta(days=365)
    )
    query = query.filter(Message.received >= since_datetime)

    # Optionally filter out messages newer than `untildays`
    if until:
        query = query.filter(Message.received <= until)

    # Optionally filter by facility
    if facility:
        query = query.filter(Message.facility == facility)

    # Optionally filter by message status
    if status:
        query = query.filter(Message.msg_status == status)

    if nis:
        query = query.filter(Message.ni.in_(nis))

    if sort_query:
        query = query.order_by(Message.received.desc())

    query = _apply_query_permissions(query, user)
    return query


def get_errors_history(
    errorsdb: Session,
    user: UKRDCUser,
    status: str = "ERROR",
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    query = errorsdb.query(
        func.date_trunc("day", Message.received),
        Message.facility,
        Message.msg_status,
        func.count(Message.received),
    )

    query = _apply_query_permissions(query, user)

    if facility:
        query = query.filter(Message.facility == facility)

    if status:
        query = query.filter(Message.msg_status == status)

    # Default to showing last 365 days
    since_datetime: datetime.datetime = (
        since or datetime.datetime.utcnow() - datetime.timedelta(days=365)
    )
    query = query.filter(func.date_trunc("day", Message.received) >= since_datetime)

    # Optionally filter out messages newer than `untildays`
    if until:
        query = query.filter(func.date_trunc("day", Message.received) <= until)

    query = query.group_by(
        func.date_trunc("day", Message.received), Message.facility, Message.msg_status
    )
    return query


def get_error(
    errorsdb: Session, jtrace: Session, error_id: str, user: UKRDCUser
) -> ExtendedErrorSchema:
    """Get an error by error_id, and convert to an ExtendedError object

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): SQLAlchemy session for the EMPI
        error_id (str): Error ID to retreive
        user (UKRDCUser): Logged-in user

    Returns:
        ExtendedErrorSchema: Error message object
    """
    error = errorsdb.query(Message).get(error_id)
    if not error:
        raise HTTPException(404, detail="Error record not found")
    _assert_permission(error, user)

    return make_extended_error(MessageSchema.from_orm(error), jtrace)

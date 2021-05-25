import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
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
        raise HTTPException(
            403,
            detail="You do not have permission to access this resource. Sending facility does not match.",
        )


def get_errors(
    errorsdb: Session,
    user: UKRDCUser,
    status: str = "ERROR",
    nis: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
):
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

    # Sort
    query = query.order_by(Message.received.desc())
    query = _apply_query_permissions(query, user)
    return query


def get_error(
    errorsdb: Session, jtrace: Session, error_id: str, user: UKRDCUser
) -> ExtendedErrorSchema:
    error = errorsdb.query(Message).get(error_id)
    if not error:
        raise HTTPException(404, detail="Error record not found")
    _assert_permission(error, user)

    return make_extended_error(MessageSchema.from_orm(error), jtrace)

import datetime
from typing import Optional

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.utils.sort import make_sqla_sorter

ERROR_SORTER = make_sqla_sorter(
    [Message.id, Message.received, Message.ni], default_sort_by=Message.received
)


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


def get_messages(
    errorsdb: Session,
    user: UKRDCUser,
    statuses: Optional[list[str]] = None,
    nis: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get a list of error messages from the errorsdb

    Args:
        errorsdb (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user
        status (Optional[list[str]], optional: Status code to filter by. Defaults to "ERROR".
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
    if statuses is not None:
        query = query.filter(Message.msg_status.in_(statuses))

    if nis:
        query = query.filter(Message.ni.in_(nis))

    query = _apply_query_permissions(query, user)
    return query


def get_message(errorsdb: Session, message_id: int, user: UKRDCUser) -> Message:
    """Get an error by message_id

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): SQLAlchemy session for the EMPI
        message_id (str): Error ID to retreive
        user (UKRDCUser): Logged-in user

    Returns:
        Message: Error message object
    """
    error = errorsdb.query(Message).get(message_id)
    if not error:
        raise ResourceNotFoundError("Error record not found")
    _assert_permission(error, user)

    return error


def get_messages_related_to_masterrecord(
    errorsdb: Session,
    jtrace: Session,
    record_id: int,
    user: UKRDCUser,
    statuses: Optional[list[str]] = None,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
) -> Query:
    """Get a list of error messages from the errorsdb

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        user (UKRDCUser): Logged-in user
        record_id (int): MasterRecord ID
        status (str, optional): Status code to filter by. Defaults to all.
        facility (Optional[str], optional): Unit/facility code to filter by. Defaults to None.
        since (Optional[datetime.datetime], optional): Show records since datetime. Defaults to 365 days ago.
        until (Optional[datetime.datetime], optional): Show records until datetime. Defaults to None.

    Returns:
        Query: SQLAlchemy query
    """
    related_master_records = get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user
    )

    related_national_ids: list[str] = [
        record.nationalid for record in related_master_records.all()
    ]

    return get_messages(
        errorsdb,
        user,
        statuses=statuses,
        nis=related_national_ids,
        facility=facility,
        since=since,
        until=until,
    )


def get_last_message_on_masterrecord(
    jtrace: Session, errorsdb: Session, record_id: int, user: UKRDCUser
) -> Optional[Message]:
    """
    Return a summary of the most recent file received for a MasterRecord,
    within the last year

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): SQLAlchemy session
        record_id (int): MasterRecord ID
        user (UKRDCUser): User object

    Returns:
        MasterRecord: MasterRecord
    """
    record: MasterRecord = get_masterrecord(jtrace, record_id, user)

    msgs = (
        get_messages_related_to_masterrecord(
            errorsdb,
            jtrace,
            record.id,
            user,
            since=datetime.datetime.utcnow() - datetime.timedelta(days=365),
        )
        .filter(Message.facility != "TRACING")
        .filter(Message.filename.isnot(None))
    )
    return msgs.order_by(Message.received.desc()).first()

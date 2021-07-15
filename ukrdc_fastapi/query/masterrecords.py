import datetime
from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError, person_belongs_to_units
from ukrdc_fastapi.query.errors import get_errors
from ukrdc_fastapi.schemas.errors import MessageSchema, MinimalMessageSchema
from ukrdc_fastapi.utils.links import find_related_ids


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return (
        query.join(LinkRecord)
        .join(Person)
        .join(PidXRef)
        .filter(PidXRef.sending_facility.in_(units))
    )


def _assert_permission(record: MasterRecord, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    link: LinkRecord
    for link in record.link_records:
        person: Person = link.person
        if person_belongs_to_units(person, units):
            return

    raise PermissionsError()


def get_masterrecords(
    jtrace: Session,
    user: UKRDCUser,
    facility: Optional[str] = None,
) -> Query:
    """Get a list of MasterRecords from the EMPI

    Args:
        jtrace (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object
        facility (Optional[str], optional): Facility code to get records from. Defaults to None.

    Returns:
        Query: SQLALchemy query
    """
    records = jtrace.query(MasterRecord)

    if facility:
        records = (
            records.join(LinkRecord)
            .join(Person)
            .join(PidXRef)
            .filter(PidXRef.sending_facility == facility)
        )

    return _apply_query_permissions(records, user)


def get_masterrecord(jtrace: Session, record_id: int, user: UKRDCUser) -> MasterRecord:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (int): MasterRecord ID
        user (UKRDCUser): User object

    Returns:
        MasterRecord: MasterRecord
    """
    record: Optional[MasterRecord] = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")
    _assert_permission(record, user)
    return record


def get_masterrecords_related_to_masterrecord(
    jtrace: Session, record_id: int, user: UKRDCUser
) -> Query:
    """Get a query of MasterRecords related via the LinkRecord network to a given MasterRecord

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (int): MasterRecord ID
        user (UKRDCUser): Logged-in user

    Returns:
        Query: SQLAlchemy query
    """
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(jtrace, {record_id}, set())
    # Return a jtrace query of the matched master records
    records = jtrace.query(MasterRecord).filter(MasterRecord.id.in_(related_master_ids))

    return _apply_query_permissions(records, user)


def get_errors_related_to_masterrecord(
    errorsdb: Session,
    jtrace: Session,
    user: UKRDCUser,
    record_id: int,
    status: Optional[str] = "ERROR",
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
        status (str, optional): Status code to filter by. Defaults to "ERROR".
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

    return get_errors(
        errorsdb,
        user,
        status=status,
        nis=related_national_ids,
        facility=facility,
        since=since,
        until=until,
    )


def get_last_message_on_masterrecord(
    jtrace: Session, errorsdb: Session, record_id: int, user: UKRDCUser
) -> Optional[Message]:
    """
    Return a summary of the most recent file recieved for a MasterRecord,
    within the last year

    Args:
        errorsdb (Session): SQLAlchemy session
        jtrace (Session): SQLAlchemy session
        record_id (int): MasterRecord ID
        user (UKRDCUser): User object

    Returns:
        MasterRecord: MasterRecord
    """
    record: Optional[MasterRecord] = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")
    _assert_permission(record, user)

    msgs = get_errors_related_to_masterrecord(
        errorsdb,
        jtrace,
        user,
        record.id,
        status=None,
        since=datetime.datetime.utcnow() - datetime.timedelta(days=365),
    ).filter(Message.facility != "TRACING")
    return msgs.order_by(Message.received.desc()).first()

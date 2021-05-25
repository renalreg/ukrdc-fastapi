from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
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
        xref: PidXRef
        for xref in person.xref_entries:
            if xref.sending_facility in units:
                return

    raise HTTPException(
        403,
        detail=f"You do not have permission to access this resource. Sending facility does not match.",
    )


def get_masterrecords(
    jtrace: Session,
    user: UKRDCUser,
    facility: Optional[str] = None,
):
    """Retreive a list of master records from the EMPI"""
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

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        MasterRecord: MasterRecord
    """
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")
    _assert_permission(record, user)
    return record


def get_masterrecords_related_to_masterrecord(
    jtrace: Session, record_id: int, user: UKRDCUser
) -> Query:
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(jtrace, {record_id}, set())
    # Return a jtrace query of the matched master records
    records = jtrace.query(MasterRecord).filter(MasterRecord.id.in_(related_master_ids))

    return _apply_query_permissions(records, user)

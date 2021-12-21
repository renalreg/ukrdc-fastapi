from typing import Optional

from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef
from ukrdc_sqla.utils.links import (
    PersonMasterLink,
    find_related_ids,
    find_related_link_records,
)

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.query.common import PermissionsError, person_belongs_to_units
from ukrdc_fastapi.query.persons import get_person


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
) -> Query:
    """Get a list of MasterRecords from the EMPI

    Args:
        jtrace (Session): SQLALchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        Query: SQLALchemy query
    """
    return _apply_query_permissions(jtrace.query(MasterRecord), user)


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
    jtrace: Session, record_id: int, user: UKRDCUser, exclude_self: bool = False
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

    # Exclude self from related items
    if exclude_self:
        records = records.filter(MasterRecord.id != record_id)

    return _apply_query_permissions(records, user)


def get_masterrecords_related_to_person(
    jtrace: Session,
    person_id: int,
    user: UKRDCUser,
    nationalid_type: Optional[str] = None,
) -> Query:
    """Get a query of MasterRecords related via the LinkRecord network to a given Person

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        person_id (int): Person ID
        user (UKRDCUser): Logged-in user
        nationalid_type (str, optional): National ID type to filter by. E.g. "UKRDC"

    Returns:
        Query: SQLAlchemy query
    """
    person = get_person(jtrace, person_id, user)

    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: set[PersonMasterLink] = find_related_link_records(
        jtrace, person_id=person.id
    )

    # Find all related master records within the UKRDC
    master_with_ukrdc = jtrace.query(MasterRecord).filter(
        MasterRecord.id.in_([link.master_id for link in related_person_master_links])
    )

    if nationalid_type:
        master_with_ukrdc = master_with_ukrdc.filter(
            MasterRecord.nationalid_type == nationalid_type
        )

    return master_with_ukrdc

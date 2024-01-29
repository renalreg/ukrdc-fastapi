from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.empi import MasterRecord, Person
from ukrdc_sqla.utils.links import (
    PersonMasterLink,
    find_related_ids,
    find_related_link_records,
)


def select_masterrecords_related_to_masterrecord(
    record: MasterRecord,
    jtrace: Session,
    exclude_self: bool = False,
    nationalid_type: Optional[str] = None,
) -> Select:
    """Get a query of MasterRecords related via the LinkRecord network to a given MasterRecord

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (int): MasterRecord ID
        nationalid_type (str, optional): National ID type to filter by. E.g. "UKRDC"
        exclude_self (bool, optional): Exclude the given MasterRecord from the results

    Returns:
        Query: SQLAlchemy query
    """
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(
        jtrace, {record.id} if record.id else set(), set()
    )
    # Return a select of the matched master records
    records = select(MasterRecord).where(MasterRecord.id.in_(related_master_ids))

    # Exclude self from related items
    if exclude_self:
        records = records.where(MasterRecord.id != record.id)

    # Optionally filter by record type
    if nationalid_type:
        records = records.where(MasterRecord.nationalid_type == nationalid_type)

    return records


def select_masterrecords_related_to_person(
    person: Person,
    jtrace: Session,
    nationalid_type: Optional[str] = None,
) -> Select:
    """Get a query of MasterRecords related via the LinkRecord network to a given Person

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        person_id (int): Person ID
        nationalid_type (str, optional): National ID type to filter by. E.g. "UKRDC"

    Returns:
        Query: SQLAlchemy query
    """
    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: set[PersonMasterLink] = find_related_link_records(
        jtrace, person_id=person.id
    )

    # Find all related master records within the UKRDC
    records = select(MasterRecord).where(
        MasterRecord.id.in_([link.master_id for link in related_person_master_links])
    )

    if nationalid_type:
        records = records.where(MasterRecord.nationalid_type == nationalid_type)

    return records

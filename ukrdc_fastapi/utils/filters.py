from collections import namedtuple
from typing import Optional

from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, WorkItem

PersonMasterLink = namedtuple("PersonMasterLink", ("id", "person_id", "master_id"))


def _find_related_ids(
    jtrace: Session, seen_master_ids: set[int], seen_person_ids: set[int]
):
    found_new: bool = True
    while found_new:
        links: list[LinkRecord] = (
            jtrace.query(LinkRecord)
            .filter(
                (LinkRecord.master_id.in_(seen_master_ids))
                | (LinkRecord.person_id.in_(seen_person_ids))
            )
            .all()
        )

        master_ids: set[int] = {item.master_id for item in links}
        person_ids: set[int] = {item.person_id for item in links}
        if seen_master_ids.issuperset(master_ids) and seen_person_ids.issuperset(
            person_ids
        ):
            found_new = False
        seen_master_ids |= master_ids
        seen_person_ids |= person_ids
    return (seen_master_ids, seen_person_ids)


def find_ids_related_to_person(
    localid: list[str], jtrace: Session, localid_type: Optional[str] = None
) -> tuple[set[int], set[int]]:
    """Find all person IDs and master record IDs related to a given person localid"""
    person_filters = [Person.localid.in_(localid)]
    if localid_type:
        person_filters.append(Person.localid_type.is_(localid_type))
    records: list[tuple[int]] = jtrace.query(Person.id).filter(*person_filters).all()
    flat_ids: list[int] = [personid for personid, in records]

    return _find_related_ids(jtrace, set(), set(flat_ids))


def find_ids_related_to_masterrecord(
    nationalid: list[str], jtrace: Session, nationalid_type: Optional[str] = None
) -> tuple[set[int], set[int]]:
    """Find all person IDs and master record IDs related to a given master record nationalid"""
    master_record_filters = [MasterRecord.nationalid.in_(nationalid)]
    if nationalid_type:
        master_record_filters.append(MasterRecord.nationalid_type.is_(nationalid_type))
    records: list[tuple[int]] = (
        jtrace.query(MasterRecord.id).filter(*master_record_filters).all()
    )
    flat_ids: list[int] = [masterid for masterid, in records]

    return _find_related_ids(jtrace, set(flat_ids), set())


def find_related_link_records(
    session: Session, master_id: str, person_id: Optional[str] = None
) -> set[PersonMasterLink]:
    """
    Return a list of person <-> masterrecord LinkRecord IDs
    This function is non-trivial since linked records can
    form a kind of "web". E.g:
    For master records M{n}, link records L{n}, and Person records P{n},
    we could have
    M1 <-> L1 <-> P1 <-> L2 <-> M2 <-> L3 <-> P2 etc etc
    This function basically follows the complete chain.
    """

    linkrecord_ids: set[PersonMasterLink] = set()
    new_entries: set[tuple[str, str]] = set()
    entries: Query

    # If no explicit person_id is give, we'll derive one
    if person_id:
        entries = session.query(LinkRecord).filter(
            LinkRecord.master_id == master_id, LinkRecord.person_id == person_id
        )
        new_entries = {(person_id, master_id)}
    else:
        entries = session.query(LinkRecord).filter(LinkRecord.master_id == master_id)
        new_entries = {(entry.person_id, entry.master_id) for entry in entries}

    # Add LinkRecord IDs to our output set
    linkrecord_ids |= {
        PersonMasterLink(entry.id, entry.person_id, entry.master_id)
        for entry in entries
    }

    # For each personid-masterid tuple
    while new_entries:
        # Remove the element from the set
        person_id, master_id = new_entries.pop()

        # Filter every possible LinkRecord by personid OR masterid
        link_records: Query = session.query(LinkRecord).filter(
            (LinkRecord.person_id == person_id) | (LinkRecord.master_id == master_id)
        )

        # For each match (either personid or masterid)
        for record in link_records:
            person_master_link: PersonMasterLink = PersonMasterLink(
                record.id, record.person_id, record.master_id
            )
            # If it's already in the original set, skip
            if person_master_link in linkrecord_ids:
                continue
            # Add the matched entry to the set we're iterating through
            new_entries.add((record.person_id, record.master_id))
            # Add the LinkRecord ID to our output
            linkrecord_ids.add(person_master_link)

    return linkrecord_ids


def workitems_by_ukrdcids(session: Session, query: Query, ukrdcids: list[str]) -> Query:
    """Filter a query of WorkItem objects by list of UKRDC IDs

    Args:
        session (Session): JTrace Session
        query (Query): Current session query to filter
        ukrdcids (list[str]): list of UKRDC IDs to filter by

    Returns:
        Query: A new query containing filtered results
    """
    # Fetch a list of master/person IDs related to each UKRDCID
    seen_master_ids: set[int]
    seen_person_ids: set[int]
    seen_master_ids, seen_person_ids = find_ids_related_to_masterrecord(
        ukrdcids, session, nationalid_type="UKRDC"
    )

    # Filter workitems by the matching IDs
    return query.filter(
        (WorkItem.master_id.in_(seen_master_ids))
        | (WorkItem.person_id.in_(seen_person_ids))
    )

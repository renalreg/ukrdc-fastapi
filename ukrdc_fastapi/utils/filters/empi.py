from collections import namedtuple
from typing import Optional

from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef

PersonMasterLink = namedtuple("PersonMasterLink", ("id", "person_id", "master_id"))


def find_related_ids(
    jtrace: Session, seen_master_ids: set[int], seen_person_ids: set[int]
):
    """
    Construct sets of related master records and person records.
    This performs a recursive search of associated link records,
    fetching the master and person record IDs from each link record.

    NOTE: (JTC. 2021-05-14) I tried replacing this code with a
    self-contained SQL query, using a CTE query, see:
    https://github.com/renalreg/ukrdc-fastapi/commit/cd46897ccf0a88c1996c72f91bc0dc5c1837b643

    However, this actually made it slower, I think because it will
    keep running until every possible link in the network has been
    found, whereas here we can skip nodes if no new record IDs are
    found? I'm not totally sure the reason, but it does make me wonder
    if this function might miss results. The commit linked above
    can be used if this is found to be the case, but note that it
    will slow this function down by around 1.5x
    """
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


def find_persons_related_to_masterrecord(
    initial_record: MasterRecord, jtrace: Session
) -> Query:
    """Given an input MasterRecord, recursively find all related Person records

    Args:
        initial_record (MasterRecord): Starting point of search
        jtrace (Session): EMPI database session

    Returns:
        Query: EMPI database query of all related records
    """
    # Find all related person record IDs by recursing through link records
    _, related_person_ids = find_related_ids(jtrace, {initial_record.id}, set())
    # Return a jtrace query of the matched person records
    return jtrace.query(Person).filter(Person.id.in_(related_person_ids))


def find_masterrecords_related_to_person(
    initial_record: Person, jtrace: Session
) -> Query:
    """Given an input Person record, recursively find all related MasterRecords

    Args:
        initial_record (Person): Starting point of search
        jtrace (Session): EMPI database session

    Returns:
        Query: EMPI database query of all related records
    """
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(jtrace, set(), {initial_record.id})
    # Return a jtrace query of the matched master records
    return jtrace.query(MasterRecord).filter(MasterRecord.id.in_(related_master_ids))


def find_related_masterrecords(initial_record: MasterRecord, jtrace: Session) -> Query:
    """Given an input MasterRecord, recursively find all related MasterRecords

    Args:
        initial_record (MasterRecord): Starting point of search
        jtrace (Session): EMPI database session

    Returns:
        Query: EMPI database query of all related records
    """
    # Find all related master record IDs by recursing through link records
    related_master_ids, _ = find_related_ids(jtrace, {initial_record.id}, set())
    # Return a jtrace query of the matched master records
    return jtrace.query(MasterRecord).filter(MasterRecord.id.in_(related_master_ids))


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


def filter_masterrecords_by_facility(records: Query, facility: str) -> Query:
    """
    Given a query of MasterRecords, filter the query by sending facility.
    If multiple facilities send to the same masterrecord, the record will
    be included for each.

    Args:
        records (Query): SQLAlchemy query of MasterRecords
        facility (str): Facility code/ID

    Returns:
        Query: Filtered MasterRecord query
    """
    return (
        records.join(LinkRecord)
        .join(Person)
        .join(PidXRef)
        .filter(PidXRef.sending_facility == facility)
    )

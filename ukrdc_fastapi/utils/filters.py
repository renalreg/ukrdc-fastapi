from collections import namedtuple
from typing import List, Optional, Set, Tuple

from sqlalchemy.orm import Query, Session

from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, WorkItem
from ukrdc_fastapi.models.ukrdc import PatientNumber, PatientRecord

PersonMasterLink = namedtuple("PersonMasterLink", ("id", "person_id", "master_id"))


def _find_related_ids(ukrdcid: List[str], jtrace: Session) -> Tuple[Set[int], Set[int]]:
    records: List[Tuple[int]] = (
        jtrace.query(MasterRecord.id)
        .filter(
            MasterRecord.nationalid_type == "UKRDC",
            MasterRecord.nationalid.in_(ukrdcid),
        )
        .all()
    )
    flat_ids: List[int] = [masterid for masterid, in records]

    seen_master_ids: Set[int] = set(flat_ids)
    seen_person_ids: Set[int] = set()
    found_new: bool = True
    while found_new:
        links: List[LinkRecord] = (
            jtrace.query(LinkRecord)
            .filter(
                (LinkRecord.master_id.in_(seen_master_ids))
                | (LinkRecord.person_id.in_(seen_person_ids))
            )
            .all()
        )

        master_ids: Set[int] = {item.master_id for item in links}
        person_ids: Set[int] = {item.person_id for item in links}
        if seen_master_ids.issuperset(master_ids) and seen_person_ids.issuperset(
            person_ids
        ):
            found_new = False
        seen_master_ids |= master_ids
        seen_person_ids |= person_ids
    return (seen_master_ids, seen_person_ids)


def find_related_link_records(
    session: Session, master_id: str, person_id: Optional[str] = None
) -> Set[PersonMasterLink]:
    """
    Return a list of person <-> masterrecord LinkRecord IDs
    This function is non-trivial since linked records can
    form a kind of "web". E.g:
    For master records M{n}, link records L{n}, and Person records P{n},
    we could have
    M1 <-> L1 <-> P1 <-> L2 <-> M2 <-> L3 <-> P2 etc etc
    This function basically follows the complete chain.
    """

    linkrecord_ids: Set[PersonMasterLink] = set()
    new_entries: Set[Tuple[str, str]] = set()

    # If no explicit person_id is give, we'll derive one
    if person_id:
        new_entries = {(person_id, master_id)}
    else:
        entries: Query = session.query(LinkRecord).filter(
            LinkRecord.master_id == master_id
        )

        # Set of personid-masterid tuples from query
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


def patientrecords_by_ni(session: Session, query: Query, patientid: str) -> Query:
    """Filter a query of PatientRecord objects by a given NI patient ID

    Args:
        session (Session): UKRDC session
        query (Query): Current session query to filter
        patientid (str): NI patient ID to filter by

    Returns:
        Query: A new query containing filtered results
    """
    pids: Query = session.query(PatientNumber.pid).filter(
        PatientNumber.patientid == patientid,
        PatientNumber.numbertype == "NI",
    )

    # Find different ukrdcids
    ukrdcid_query: Query = (
        session.query(PatientRecord.ukrdcid)
        .filter(PatientRecord.pid.in_(pids))
        .distinct()
    )
    ukrdcids: List[str] = [ukrdcid for (ukrdcid,) in ukrdcid_query.all()]

    # Find all the records with ukrdc ids
    return query.filter(PatientRecord.ukrdcid.in_(ukrdcids))


def linkrecords_by_ni(session: Session, query: Query, nationalid: str) -> Query:
    """Filter a query of LinkRecord objects by a given NI patient ID.
    Note: This works by scanning all LinkRecords to find all those
    related to the given NI, following a chain of relationships.
    The input query is then filtered by these found LinkRecords.
    This means that if you pass in an already filtered query, you
    may not get ALL related LinkRecord objects back, rather, you
    will get back the items from your original query which are related.

    Args:
        session (Session): Jtrace session
        query (Query): Current session query to filter
        nationalid (str): NI patient ID to filter by

    Returns:
        Query: A new query containing filtered results
    """
    master_records: Query = session.query(MasterRecord).filter(
        MasterRecord.nationalid == nationalid
    )
    master_ids: List[str] = [record.id for record in master_records.all()]

    link_record_ids: Set[int] = set()
    for master_id in master_ids:
        link_record_ids |= {
            pml.id for pml in find_related_link_records(session, master_id)
        }

    return query.filter(LinkRecord.id.in_(link_record_ids))


def workitems_by_ukrdcids(session: Session, query: Query, ukrdcids: List[str]) -> Query:
    """Filter a query of WorkItem objects by list of UKRDC IDs

    Args:
        session (Session): JTrace Session
        query (Query): Current session query to filter
        ukrdcids (List[str]): List of UKRDC IDs to filter by

    Returns:
        Query: A new query containing filtered results
    """
    # Fetch a list of master/person IDs related to each UKRDCID
    seen_master_ids: Set[int]
    seen_person_ids: Set[int]
    seen_master_ids, seen_person_ids = _find_related_ids(ukrdcids, session)

    # Filter workitems by the matching IDs
    return query.filter(
        (WorkItem.master_id.in_(seen_master_ids))
        | (WorkItem.person_id.in_(seen_person_ids))
    )

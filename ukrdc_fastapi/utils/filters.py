from typing import List, Set, Tuple

from sqlalchemy.orm import Query, Session

from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, WorkItem
from ukrdc_fastapi.models.ukrdc import PatientNumber, PatientRecord


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

from typing import List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, Person, WorkItem
from ukrdc_fastapi.schemas.empi import WorkItemSchema, WorkItemShortSchema

router = APIRouter()


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


@router.get("/", response_model=Page[WorkItemShortSchema])
def workitems_list(
    ukrdcid: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):

    # Get a query of all workitems
    query = jtrace.query(WorkItem)

    # If a list of UKRDCIDs is found in the query, filter by UKRDCIDs
    if ukrdcid:
        # Fetch a list of master/person IDs related to each UKRDCID
        seen_master_ids: Set[int]
        seen_person_ids: Set[int]
        seen_master_ids, seen_person_ids = _find_related_ids(ukrdcid, jtrace)

        # Filter workitems by the matching IDs
        query = query.filter(
            (WorkItem.master_id.in_(seen_master_ids))
            | (WorkItem.person_id.in_(seen_person_ids))
        )

    query = query.filter(WorkItem.status == 1).order_by(WorkItem.id)

    # Filter by status, sort, and return all
    return paginate(query)


@router.get("/{workitem_id}", response_model=WorkItemSchema)
def workitems_detail(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
):

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    other_workitems = jtrace.query(WorkItem).filter(
        WorkItem.master_id == workitem.master_id,
        WorkItem.id != workitem.id,
        WorkItem.status == 1,
    )

    # Inject related workitems
    workitem.related = other_workitems.all()
    return workitem

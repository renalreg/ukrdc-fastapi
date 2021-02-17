from typing import List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import LinkRecord, MasterRecord, WorkItem
from ukrdc_fastapi.schemas.empi import WorkItemSchema

router = APIRouter()


@router.get("/workitems", response_model=List[WorkItemSchema])
def workitems(
    self,
    ukrdcid: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
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

    workitems = jtrace.query(WorkItem).filter(
        (WorkItem.master_id.in_(seen_master_ids))
        | (WorkItem.person_id.in_(seen_person_ids))
    )
    return workitems.filter(WorkItem.status == 1).all()

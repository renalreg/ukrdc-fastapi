from typing import List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import WorkItem
from ukrdc_fastapi.schemas.empi import WorkItemSchema, WorkItemShortSchema
from ukrdc_fastapi.utils import filters

router = APIRouter()


@router.get("/", response_model=Page[WorkItemShortSchema])
def workitems_list(
    ukrdcid: Optional[List[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
    # Get a query of open workitems
    query = jtrace.query(WorkItem).filter(WorkItem.status == 1)

    # If a list of UKRDCIDs is found in the query, filter by UKRDCIDs
    if ukrdcid:
        query = filters.workitems_by_ukrdcids(jtrace, query, ukrdcid)

    # Sort, paginate, and return
    return paginate(query.order_by(WorkItem.id))


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

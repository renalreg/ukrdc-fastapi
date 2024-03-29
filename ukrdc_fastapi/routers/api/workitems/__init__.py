import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Security
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.audit import Auditer, get_auditer
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.permissions.workitems import apply_workitem_list_permission
from ukrdc_fastapi.query.workitems import select_workitems
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

from . import workitem_id

router = APIRouter(tags=["Work Items"])
router.include_router(workitem_id.router)


class UnlinkWorkItemRequestSchema(BaseModel):
    master_record: str = Field(..., title="Master record ID")
    person_id: str = Field(..., title="Person ID")
    comment: Optional[str]


@router.get(
    "",
    response_model=Page[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitems(
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[int]] = Query([1]),
    facility: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [
                WorkItem.id,
                WorkItem.last_updated,
                WorkItem.master_id,
                WorkItem.person_id,
            ],
            default_sort_by=WorkItem.last_updated,
        )
    ),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of open work items from the EMPI"""
    stmt = select_workitems(
        statuses=status or [], facility=facility, since=since, until=until
    )
    stmt = apply_workitem_list_permission(stmt, user)

    # Paginate and sort
    page = paginate(jtrace, sorter.sort(stmt))

    # Add audit events
    for item in page.items:  # type: ignore
        audit.add_workitem(item)

    return page

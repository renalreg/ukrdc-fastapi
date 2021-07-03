import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Security
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.empi import WorkItemShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import workitem_id

router = APIRouter(tags=["Patient Index/Work Items"])
router.include_router(workitem_id.router)


class UnlinkWorkItemRequestSchema(BaseModel):
    master_record: str = Field(..., title="Master record ID")
    person_id: str = Field(..., title="Person ID")
    comment: Optional[str]


@router.get(
    "/",
    response_model=Page[WorkItemShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitems_list(
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[int]] = Query([1]),
    facility: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of open work items from the EMPI"""
    return paginate(
        get_workitems(
            jtrace, user, statuses=status, facility=facility, since=since, until=until
        )
    )

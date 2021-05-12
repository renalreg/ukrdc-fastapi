import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from httpx import Response
from mirth_client import MirthAPI
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, User, auth
from ukrdc_fastapi.schemas.empi import WorkItemShortSchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_unlink_message,
    get_channel_from_name,
)
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
    ukrdcid: Optional[list[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of open work items from the EMPI"""
    workitems = jtrace.query(WorkItem)

    # Optionally filter Workitems updated since
    if since:
        workitems = workitems.filter(WorkItem.last_updated >= since)

    # Optionally filter Workitems updated before
    if until:
        workitems = workitems.filter(WorkItem.last_updated <= until)

    # Get a query of open workitems
    workitems = workitems.filter(WorkItem.status.in_(status))

    # If a list of UKRDCIDs is found in the query, filter by UKRDCIDs
    if ukrdcid:
        workitems = filters.workitems_by_ukrdcids(jtrace, workitems, ukrdcid)

    # Sort, paginate, and return
    return paginate(workitems.order_by(WorkItem.last_updated.desc()))


@router.post(
    "/unlink/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitems_unlink(
    args: UnlinkWorkItemRequestSchema,
    user: User = Security(auth.get_user),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Unlink any master record and person record"""

    channel = await get_channel_from_name("Unlink", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for Unlink channel not found"
        )  # pragma: no cover

    message: str = build_unlink_message(
        args.master_record, args.person_id, user.email, args.comment
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)

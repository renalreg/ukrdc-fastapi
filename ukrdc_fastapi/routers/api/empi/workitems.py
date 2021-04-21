import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi_auth0 import Auth0User
from httpx import Response
from mirth_client import Channel, MirthAPI
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.schemas.empi import WorkItemSchema, WorkItemShortSchema
from ukrdc_fastapi.utils import filters, mirth, parse_date
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_close_workitem_message,
    build_merge_message,
    build_unlink_message,
    build_update_workitem_message,
    get_channel_from_name,
)
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


class UnlinkWorkItemRequestSchema(BaseModel):
    master_record: str = Field(..., title="Master record ID")
    person_id: str = Field(..., title="Person ID")
    comment: Optional[str]


class CloseWorkItemRequestSchema(BaseModel):
    comment: Optional[str]


class UpdateWorkItemRequestSchema(BaseModel):
    status: Optional[int] = None
    comment: Optional[str] = None


@router.get("/", response_model=Page[WorkItemShortSchema])
def workitems_list(
    since: Optional[str] = None,
    until: Optional[str] = None,
    status: Optional[list[int]] = Query([1]),
    ukrdcid: Optional[list[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_WORKITEMS]),
):
    """Retreive a list of open work items from the EMPI"""
    workitems = jtrace.query(WorkItem)

    # Optionally filter Workitems updated since
    if since:
        since_datetime: Optional[datetime.datetime] = parse_date(since)
        if since_datetime:
            workitems = workitems.filter(WorkItem.last_updated >= since_datetime)

    # Optionally filter Workitems updated before
    if until:
        until_datetime: Optional[datetime.datetime] = parse_date(until)
        if until_datetime:
            workitems = workitems.filter(
                WorkItem.last_updated <= until_datetime + datetime.timedelta(days=1)
            )

    # Get a query of open workitems
    workitems = workitems.filter(WorkItem.status.in_(status))

    # If a list of UKRDCIDs is found in the query, filter by UKRDCIDs
    if ukrdcid:
        workitems = filters.workitems_by_ukrdcids(jtrace, workitems, ukrdcid)

    # Sort, paginate, and return
    return paginate(workitems.order_by(WorkItem.last_updated.desc()))


@router.get("/{workitem_id}/", response_model=WorkItemSchema)
def workitem_detail(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_WORKITEMS]),
):
    """Retreive a particular work item from the EMPI"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    return workitem


@router.put("/{workitem_id}/", response_model=MirthMessageResponseSchema)
async def workitem_update(
    workitem_id: int,
    args: UpdateWorkItemRequestSchema,
    user: Auth0User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_WORKITEMS, Scopes.WRITE_WORKITEMS]
    ),
):
    """Update a particular work item in the EMPI"""
    print("Updating workitem")
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("WorkItemUpdate", mirth, redis)

    if not channel:
        raise HTTPException(500, detail="ID for WorkItemUpdate channel not found")

    message: str = build_update_workitem_message(
        workitem.id,
        args.status or workitem.status,
        args.comment or workitem.description,
        user.email,
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.get("/{workitem_id}/related/", response_model=list[WorkItemSchema])
def workitem_related(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_WORKITEMS]),
):
    """Retreive a list of other work items related to a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    other_workitems = jtrace.query(WorkItem).filter(
        WorkItem.master_id == workitem.master_id,
        WorkItem.id != workitem.id,
        WorkItem.status == 1,
    )

    return other_workitems.all()


@router.post("/{workitem_id}/close/", response_model=MirthMessageResponseSchema)
async def workitem_close(
    workitem_id: int,
    args: CloseWorkItemRequestSchema,
    jtrace: Session = Depends(get_jtrace),
    user: Auth0User = Security(auth.get_user),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_WORKITEMS, Scopes.WRITE_WORKITEMS]
    ),
):
    """Update and close a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("WorkItemUpdate", mirth, redis)
    if not channel:
        raise HTTPException(500, detail="ID for WorkItemUpdate channel not found")

    message: str = build_close_workitem_message(
        workitem.id, args.comment or "", user.email
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/{workitem_id}/merge/", response_model=MirthMessageResponseSchema)
async def workitem_merge(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_WORKITEMS, Scopes.WRITE_WORKITEMS]
    ),
):
    """Merge a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: set[
        filters.PersonMasterLink
    ] = filters.find_related_link_records(
        jtrace, workitem.master_id, person_id=workitem.person_id
    )

    # Find all related master records within the UKRDC
    master_with_ukrdc = (
        jtrace.query(MasterRecord)
        .filter(
            MasterRecord.id.in_(
                [link.master_id for link in related_person_master_links]
            )
        )
        .filter(MasterRecord.nationalid_type == "UKRDC")
        .order_by(MasterRecord.id)
        .all()
    )

    # If we don't have 2 records, something has gone wrong
    if len(master_with_ukrdc) != 2:
        raise HTTPException(
            400,
            detail=f"Got {len(master_with_ukrdc)} master record(s) with different UKRDC IDs. Expected 2.",
        )

    channel = await get_channel_from_name("Merge Patient", mirth, redis)
    if not channel:
        raise HTTPException(500, detail="ID for Merge Patient channel not found")

    message: str = build_merge_message(
        superceding=master_with_ukrdc[0].id, superceeded=master_with_ukrdc[1].id
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/{workitem_id}/unlink/", response_model=MirthMessageResponseSchema)
async def workitem_unlink(
    workitem_id: int,
    user: Auth0User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_WORKITEMS, Scopes.WRITE_WORKITEMS]
    ),
):
    """Unlink the master record and person record in a particular work item"""

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("Unlink", mirth, redis)
    if not channel:
        raise HTTPException(500, detail="ID for Unlink channel not found")

    message: str = build_unlink_message(
        workitem.master_id, workitem.person_id, user.email
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/unlink/", response_model=MirthMessageResponseSchema)
async def workitems_unlink(
    args: UnlinkWorkItemRequestSchema,
    user: Auth0User = Security(auth.get_user),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_WORKITEMS, Scopes.WRITE_WORKITEMS]
    ),
):
    """Unlink any master record and person record"""

    channel = await get_channel_from_name("Unlink", mirth, redis)
    if not channel:
        raise HTTPException(500, detail="ID for Unlink channel not found")

    message: str = build_unlink_message(
        args.master_record, args.person_id, user.email, args.comment
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)

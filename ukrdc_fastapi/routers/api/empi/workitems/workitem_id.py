from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from httpx import Response
from mirth_client import MirthAPI
from pydantic import BaseModel
from redis import Redis
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, User, auth
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.utils.filters.empi import PersonMasterLink, find_related_link_records
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_close_workitem_message,
    build_merge_message,
    build_unlink_message,
    build_update_workitem_message,
    get_channel_from_name,
)

router = APIRouter(prefix="/{workitem_id}")


class CloseWorkItemRequestSchema(BaseModel):
    comment: Optional[str]


class UpdateWorkItemRequestSchema(BaseModel):
    status: Optional[int] = None
    comment: Optional[str] = None


@router.get(
    "/",
    response_model=WorkItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_detail(workitem_id: int, jtrace: Session = Depends(get_jtrace)):
    """Retreive a particular work item from the EMPI"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    return workitem


@router.put(
    "/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitem_update(
    workitem_id: int,
    args: UpdateWorkItemRequestSchema,
    user: User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Update a particular work item in the EMPI"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("WorkItemUpdate", mirth, redis)

    if not channel:
        raise HTTPException(
            500, detail="ID for WorkItemUpdate channel not found"
        )  # pragma: no cover

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


@router.get(
    "/related/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_related(workitem_id: int, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of other work items related to a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    other_workitems = jtrace.query(WorkItem).filter(
        or_(
            WorkItem.master_id == workitem.master_id,
            WorkItem.person_id == workitem.person_id,
        ),
        WorkItem.id != workitem.id,
        WorkItem.status == 1,
    )

    return other_workitems.all()


@router.post(
    "/close/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitem_close(
    workitem_id: int,
    args: CloseWorkItemRequestSchema,
    jtrace: Session = Depends(get_jtrace),
    user: User = Security(auth.get_user),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Update and close a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("WorkItemUpdate", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for WorkItemUpdate channel not found"
        )  # pragma: no cover

    message: str = build_close_workitem_message(
        workitem.id, args.comment or "", user.email
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/merge/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitem_merge(
    workitem_id: int,
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Merge a particular work item"""
    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: set[PersonMasterLink] = find_related_link_records(
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
        raise HTTPException(
            500, detail="ID for Merge Patient channel not found"
        )  # pragma: no cover

    message: str = build_merge_message(
        superceding=master_with_ukrdc[0].id, superceeded=master_with_ukrdc[1].id
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/unlink/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitem_unlink(
    workitem_id: int,
    user: User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Unlink the master record and person record in a particular work item"""

    workitem = jtrace.query(WorkItem).get(workitem_id)
    if not workitem:
        raise HTTPException(404, detail="Work item not found")

    channel = await get_channel_from_name("Unlink", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for Unlink channel not found"
        )  # pragma: no cover

    message: str = build_unlink_message(
        workitem.master_id, workitem.person_id, user.email
    )

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)

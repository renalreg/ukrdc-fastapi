import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from mirth_client import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.messages import get_messages
from ukrdc_fastapi.query.mirth.merge import merge_person_into_master_record
from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record
from ukrdc_fastapi.query.mirth.workitems import close_workitem, update_workitem
from ukrdc_fastapi.query.workitems import (
    get_workitem,
    get_workitems_related_to_workitem,
)
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(prefix="/{workitem_id}")


class CloseWorkItemRequestSchema(JSONModel):
    comment: Optional[str]


class UpdateWorkItemRequestSchema(JSONModel):
    status: Optional[int] = None
    comment: Optional[str] = None


@router.get(
    "/",
    response_model=WorkItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_detail(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular work item from the EMPI"""
    return get_workitem(jtrace, workitem_id, user)


@router.put(
    "/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.WRITE_WORKITEMS,
                    auth.permissions.WRITE_EMPI,
                ]
            )
        )
    ],
)
async def workitem_update(
    workitem_id: int,
    args: UpdateWorkItemRequestSchema,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Update a particular work item in the EMPI"""

    return await update_workitem(
        jtrace,
        workitem_id,
        user,
        mirth,
        redis,
        status=args.status,
        comment=args.comment,
    )


@router.get(
    "/related/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_related(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of other work items related to a particular work item"""
    return get_workitems_related_to_workitem(jtrace, workitem_id, user).all()


@router.get(
    "/messages/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_messages(
    workitem_id: int,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Retreive a list of other work items related to a particular work item"""
    workitem = get_workitem(jtrace, workitem_id, user)
    workitem_ni: str = workitem.master_record.nationalid

    return paginate(
        get_messages(
            errorsdb,
            user,
            status=status,
            nis=[workitem_ni],
            facility=facility,
            since=since,
            until=until,
        )
    )


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
    args: Optional[CloseWorkItemRequestSchema],
    jtrace: Session = Depends(get_jtrace),
    user: UKRDCUser = Security(auth.get_user),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Update and close a particular work item"""
    workitem = get_workitem(jtrace, workitem_id, user)
    return await close_workitem(
        jtrace,
        workitem.id,
        user,
        mirth,
        redis,
        comment=(args.comment if args else None),
    )


@router.post(
    "/merge/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.WRITE_WORKITEMS,
                    auth.permissions.WRITE_EMPI,
                ]
            )
        )
    ],
)
async def workitem_merge(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Merge a particular work item"""
    workitem = get_workitem(jtrace, workitem_id, user)
    return await merge_person_into_master_record(
        workitem.person_id, workitem.master_id, user, jtrace, mirth, redis
    )


@router.post(
    "/unlink/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.WRITE_WORKITEMS,
                    auth.permissions.WRITE_EMPI,
                ]
            )
        )
    ],
)
async def workitem_unlink(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Unlink the master record and person record in a particular work item"""
    workitem = get_workitem(jtrace, workitem_id, user)
    return await unlink_person_from_master_record(
        workitem.person_id, workitem.master_id, user, jtrace, mirth, redis
    )

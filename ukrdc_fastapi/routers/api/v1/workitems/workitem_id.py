import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from mirth_client import MirthAPI
from pydantic.fields import Field
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.messages import get_messages
from ukrdc_fastapi.query.mirth.workitems import close_workitem, update_workitem
from ukrdc_fastapi.query.workitems import (
    get_extended_workitem,
    get_workitem,
    get_workitem_collection,
    get_workitems_related_to_workitem,
)
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.empi import WorkItemExtendedSchema, WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


class CloseWorkItemRequest(JSONModel):
    comment: Optional[str] = Field(None, max_length=100)


class UpdateWorkItemRequest(JSONModel):
    status: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=100)


@router.get(
    "/{workitem_id}",
    response_model=WorkItemExtendedSchema,
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular work item from the EMPI"""
    workitem_obj = get_extended_workitem(jtrace, workitem_id, user)
    audit.add_workitem(workitem_obj)
    return workitem_obj


@router.put(
    "/{workitem_id}",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.WRITE_WORKITEMS,
                    Permissions.WRITE_EMPI,
                ]
            )
        )
    ],
)
async def workitem_update(
    workitem_id: int,
    args: UpdateWorkItemRequest,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Update a particular work item in the EMPI"""

    audit.add_event(Resource.WORKITEM, workitem_id, AuditOperation.UPDATE)

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
    "/{workitem_id}/colection",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_collection(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    collection = get_workitem_collection(jtrace, workitem_id, user).all()

    for workitem_obj in collection:
        audit.add_workitem(workitem_obj)

    return collection


@router.get(
    "/{workitem_id}/related",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_related(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    related = get_workitems_related_to_workitem(jtrace, workitem_id, user).all()

    for workitem_obj in related:
        audit.add_workitem(workitem_obj)

    return related


@router.get(
    "/{workitem_id}/messages",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_messages(
    workitem_id: int,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[str]] = QueryParam(None),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    workitem_obj = get_extended_workitem(jtrace, workitem_id, user)

    workitem_nis: list[str] = [
        record.nationalid for record in workitem_obj.incoming.master_records
    ]

    if workitem_obj.master_record:
        workitem_nis.append(workitem_obj.master_record.nationalid.strip())

    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.WORKITEM, workitem_id, AuditOperation.READ),
    )

    return paginate(
        get_messages(
            errorsdb,
            user,
            statuses=status,
            nis=workitem_nis,
            facility=facility,
            since=since,
            until=until,
        )
    )


@router.post(
    "/{workitem_id}/close",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission([Permissions.READ_WORKITEMS, Permissions.WRITE_WORKITEMS])
        )
    ],
)
async def workitem_close(
    workitem_id: int,
    args: Optional[CloseWorkItemRequest],
    jtrace: Session = Depends(get_jtrace),
    user: UKRDCUser = Security(auth.get_user()),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Update and close a particular work item"""
    workitem_obj = get_workitem(jtrace, workitem_id, user)

    audit.add_event(Resource.WORKITEM, workitem_obj.id, AuditOperation.UPDATE)

    return await close_workitem(
        jtrace,
        workitem_obj.id,
        user,
        mirth,
        redis,
        comment=(args.comment if args else None),
    )

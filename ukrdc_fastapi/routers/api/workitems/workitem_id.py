import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from fastapi import Query as QueryParam
from mirth_client import MirthAPI
from pydantic.fields import Field
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.messages import apply_message_list_permissions
from ukrdc_fastapi.permissions.workitems import (
    apply_workitem_list_permission,
    assert_workitem_permission,
)
from ukrdc_fastapi.query.messages import select_messages
from ukrdc_fastapi.query.mirth.workitems import close_workitem, update_workitem
from ukrdc_fastapi.query.workitems import (
    extend_workitem,
    select_workitem_collection,
    select_workitems_related_to_workitem,
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


def _get_workitem(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular work item from the EMPI"""
    workitem_obj = jtrace.get(WorkItem, workitem_id)
    if not workitem_obj:
        raise ResourceNotFoundError("Work item not found")

    assert_workitem_permission(workitem_obj, user)

    return workitem_obj


@router.get(
    "/{workitem_id}",
    response_model=WorkItemExtendedSchema,
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem(
    workitem_obj: WorkItem = Depends(_get_workitem),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular work item from the EMPI"""
    # Extend the work item with additional information
    extended_workitem = extend_workitem(workitem_obj, jtrace)

    # Add audit event
    audit.add_workitem(extended_workitem)

    return extended_workitem


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
    args: UpdateWorkItemRequest,
    workitem_obj: WorkItem = Depends(_get_workitem),
    user: UKRDCUser = Security(auth.get_user()),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Update a particular work item in the EMPI"""

    # Add audit event
    audit.add_event(Resource.WORKITEM, workitem_obj.id, AuditOperation.UPDATE)

    return await update_workitem(
        workitem_obj,
        mirth,
        redis,
        user.email,
        status=args.status,
        comment=args.comment,
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
    args: Optional[CloseWorkItemRequest],
    workitem_obj: WorkItem = Depends(_get_workitem),
    user: UKRDCUser = Security(auth.get_user()),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Update and close a particular work item"""

    # Add audit event
    audit.add_event(Resource.WORKITEM, workitem_obj.id, AuditOperation.UPDATE)

    return await close_workitem(
        workitem_obj,
        mirth,
        redis,
        user.email,
        comment=(args.comment if args else None),
    )


@router.get(
    "/{workitem_id}/colection",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_collection(
    workitem_obj: WorkItem = Depends(_get_workitem),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    stmt = select_workitem_collection(workitem_obj, jtrace)
    stmt = apply_workitem_list_permission(stmt, user)

    collection = jtrace.scalars(stmt).all()

    # Add audit events
    for item in collection:
        audit.add_workitem(item)

    return collection


@router.get(
    "/{workitem_id}/related",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_related(
    workitem_obj: WorkItem = Depends(_get_workitem),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    stmt = select_workitems_related_to_workitem(workitem_obj, jtrace)
    stmt = apply_workitem_list_permission(stmt, user)

    related = jtrace.scalars(stmt).all()

    # Add audit events
    for item in related:
        audit.add_workitem(item)

    return related


@router.get(
    "/{workitem_id}/messages",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_messages(
    worktiem_obj: WorkItem = Depends(_get_workitem),
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

    # TODO: Move logic into a separate query function and out the router function

    # Extend the work item with additional information
    extended_workitem = extend_workitem(worktiem_obj, jtrace)

    workitem_nis: list[str] = [
        record.nationalid for record in extended_workitem.incoming.master_records
    ]

    if extended_workitem.master_record:
        workitem_nis.append(extended_workitem.master_record.nationalid.strip())

    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.WORKITEM, worktiem_obj.id, AuditOperation.READ),
    )

    # Get messages for NIs related to the work item
    stmt = select_messages(
        statuses=status,
        nis=workitem_nis,
        facility=facility,
        since=since or worktiem_obj.creation_date - datetime.timedelta(hours=12),
        until=until or worktiem_obj.creation_date + datetime.timedelta(hours=12),
    )
    stmt = apply_message_list_permissions(stmt, user)

    return paginate(errorsdb, stmt)

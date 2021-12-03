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
from ukrdc_fastapi.dependencies.audit import Auditer, AuditOperation, MessageOperation
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

router = APIRouter(prefix="/{workitem_id}")


class CloseWorkItemRequestSchema(JSONModel):
    comment: Optional[str] = Field(None, max_length=100)


class UpdateWorkItemRequestSchema(JSONModel):
    status: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=100)


@router.get(
    "/",
    response_model=WorkItemExtendedSchema,
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_detail(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(Auditer),
):
    """Retreive a particular work item from the EMPI"""
    workitem = get_extended_workitem(jtrace, workitem_id, user)

    for master_record in workitem.incoming.master_records:
        audit.add_master_record(master_record.id, AuditOperation.READ)
    for persons in workitem.destination.persons:
        audit.add_person(persons.id, AuditOperation.READ)
    audit.add_master_record(workitem.destination.master_record.id, AuditOperation.READ)
    audit.add_person(workitem.incoming.person.id, AuditOperation.READ)

    return workitem


@router.put(
    "/",
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
    args: UpdateWorkItemRequestSchema,
    user: UKRDCUser = Security(auth.get_user()),
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
    "/colection/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_collection(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(Auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    collection = get_workitem_collection(jtrace, workitem_id, user).all()

    for workitem in collection:
        audit.add_master_record(workitem.master_record.id, AuditOperation.READ)
        audit.add_person(workitem.person.id, AuditOperation.READ)

    return collection


@router.get(
    "/related/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitem_related(
    workitem_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(Auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    related = get_workitems_related_to_workitem(jtrace, workitem_id, user).all()

    for workitem in related:
        audit.add_master_record(workitem.master_record.id, AuditOperation.READ)
        audit.add_person(workitem.person.id, AuditOperation.READ)

    return related


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
    status: Optional[list[str]] = QueryParam(None),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    audit: Auditer = Depends(Auditer),
):
    """Retreive a list of other work items related to a particular work item"""
    workitem = get_extended_workitem(jtrace, workitem_id, user)

    workitem_nis: list[str] = [
        record.nationalid for record in workitem.incoming.master_records
    ]

    if workitem.master_record:
        workitem_nis.append(workitem.master_record.nationalid)

    page = paginate(
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

    for item in page.items:
        audit.add_message(item.id, MessageOperation.READ)

    return page


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
    user: UKRDCUser = Security(auth.get_user()),
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

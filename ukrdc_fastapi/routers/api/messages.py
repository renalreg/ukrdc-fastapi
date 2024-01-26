import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from mirth_client.mirth import MirthAPI
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.messages import (
    apply_message_list_permissions,
    assert_message_permissions,
)
from ukrdc_fastapi.permissions.patientrecords import apply_patientrecord_list_permission
from ukrdc_fastapi.permissions.workitems import apply_workitem_list_permission
from ukrdc_fastapi.query.messages import (
    MessageSourceSchema,
    get_message_source,
    select_messages,
)
from ukrdc_fastapi.query.patientrecords import select_patientrecords_related_to_message
from ukrdc_fastapi.query.workitems import select_workitems_related_to_message
from ukrdc_fastapi.schemas.empi import WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.sorters import ERROR_SORTER
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter

router = APIRouter(tags=["Messages"])


def _get_message(
    message_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Simple dependency to turn ID query param and User object into a Message object."""
    message_obj = errorsdb.get(Message, message_id)
    if not message_obj:
        raise ResourceNotFoundError("Message record not found")

    assert_message_permissions(message_obj, user)

    return message_obj


@router.get(
    "",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
def messages(
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[str]] = QueryParam(None),
    channel: Optional[list[str]] = QueryParam(None),
    ni: Optional[list[str]] = QueryParam([]),
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    sorter: SQLASorter = Depends(ERROR_SORTER),
    audit: Auditer = Depends(get_auditer),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    stmt = select_messages(
        statuses=status,
        channels=channel,
        nis=ni,
        facility=facility,
        since=since,
        until=until,
    )
    stmt = apply_message_list_permissions(stmt, user)

    # Add audit events
    audit.add_event(Resource.MESSAGES, None, AuditOperation.READ)

    # Sort, paginate, and return
    return paginate(errorsdb, sorter.sort(stmt))


@router.get(
    "/{message_id}",
    response_model=MessageSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
def message(
    message_obj: Message = Depends(_get_message),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive detailed information about a specific error message"""
    # For some reason the fastAPI response_model doesn't call our channel_name
    # validator, meaning we don't get a populated channel name unless we explicitly
    # call it here.
    audit.add_event(Resource.MESSAGE, message_obj.id, AuditOperation.READ)
    return MessageSchema.from_orm(message_obj)


@router.get(
    "/{message_id}/source",
    response_model=MessageSourceSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
async def message_source(
    message_obj: Message = Depends(_get_message),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive detailed information about a specific error message"""
    message_source_obj = await get_message_source(message_obj, mirth)

    # Add audit events
    audit.add_event(Resource.MESSAGE, message_obj.id, AuditOperation.READ_SOURCE)

    return message_source_obj


@router.get(
    "/{message_id}/workitems",
    response_model=list[WorkItemSchema],
    dependencies=[
        Security(
            auth.permission([Permissions.READ_MESSAGES, Permissions.READ_WORKITEMS])
        )
    ],
)
async def message_workitems(
    message_obj: Message = Depends(_get_message),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive WorkItems associated with a specific error message"""
    stmt = select_workitems_related_to_message(message_obj, jtrace)
    stmt = apply_workitem_list_permission(stmt, user)

    workitems = jtrace.scalars(stmt).all()

    # Add audit events
    message_audit = audit.add_event(
        Resource.MESSAGE, message_obj.id, AuditOperation.READ
    )
    for item in workitems:
        audit.add_workitem(item, parent=message_audit)

    return workitems


@router.get(
    "/{message_id}/patientrecords",
    response_model=list[PatientRecordSummarySchema],
    dependencies=[
        Security(auth.permission([Permissions.READ_MESSAGES, Permissions.READ_RECORDS]))
    ],
)
async def message_patientrecords(
    message_obj: Message = Depends(_get_message),
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive patient records associated with a specific error message"""
    # Get patientrecords directly referenced by the error
    if not message_obj.ni:
        return []

    # Get patientrecords referenced by the messages national identifier
    stmt = select_patientrecords_related_to_message(message_obj)
    stmt = apply_patientrecord_list_permission(stmt, user)
    records = ukrdc3.scalars(stmt).all()

    # Add audit events
    message_audit = audit.add_event(
        Resource.MESSAGE, message_obj.id, AuditOperation.READ
    )
    for record in records:
        audit.add_event(
            Resource.PATIENT_RECORD,
            record.pid,
            AuditOperation.READ,
            parent=message_audit,
        )

    return records

import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.exceptions import HTTPException
from mirth_client.mirth import MirthAPI
from mirth_client.models import ConnectorMessageData, ConnectorMessageModel
from pydantic import Field
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    MessageOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.masterrecords import apply_masterrecord_list_permissions
from ukrdc_fastapi.permissions.messages import (
    apply_message_list_permissions,
    assert_message_permissions,
)
from ukrdc_fastapi.permissions.workitems import apply_workitem_list_permission
from ukrdc_fastapi.query.messages import ERROR_SORTER, get_messages
from ukrdc_fastapi.query.workitems import get_workitems_related_to_message
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter

router = APIRouter(tags=["Messages"])


class MessageSourceSchema(OrmModel):
    """A message source file"""

    content: Optional[str] = Field(None, description="Message content")
    content_type: Optional[str] = Field(None, description="Message content type")


def _get_message(
    message_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Simple dependency to turn ID query param and User object into a Message object."""
    message_obj = errorsdb.query(Message).get(message_id)
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
    query = get_messages(
        errorsdb,
        statuses=status,
        nis=ni,
        facility=facility,
        since=since,
        until=until,
    )

    # Apply permissions
    apply_message_list_permissions(query, user)

    # Add audit events
    audit.add_event(Resource.MESSAGES, None, MessageOperation.READ)

    # Sort, paginate, and return
    return paginate(sorter.sort(query))


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
    audit.add_event(Resource.MESSAGE, message_obj.id, MessageOperation.READ)
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
    if not message_obj.channel_id:
        raise HTTPException(404, "Channel ID not found in Mirth")

    message_src = await mirth.channel(message_obj.channel_id).get_message(
        str(message_obj.message_id), include_content=True
    )
    if not message_src:
        raise HTTPException(404, "Message not found in Mirth")

    first_connector_message: ConnectorMessageModel = list(
        message_src.connector_messages.values()
    )[0]

    message_data: Optional[ConnectorMessageData] = None

    # Prioritise encoded message over raw
    if first_connector_message.encoded:
        message_data = first_connector_message.encoded
    elif first_connector_message.raw:
        message_data = first_connector_message.raw

    # If no data is available, return a valid but empty MessageSourceSchema
    if not message_data:
        return MessageSourceSchema(content=None, content_type=None)

    audit.add_event(Resource.MESSAGE, message_obj.id, MessageOperation.READ_SOURCE)

    return MessageSourceSchema(
        content=message_data.content, content_type=message_data.data_type
    )


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
    workitems = get_workitems_related_to_message(message_obj, jtrace)

    # Apply permissions
    workitems = apply_workitem_list_permission(workitems, user)

    # Add audit events
    message_audit = audit.add_event(
        Resource.MESSAGE, message_obj.id, MessageOperation.READ
    )
    for item in workitems:
        audit.add_workitem(item, parent=message_audit)

    return workitems.all()


@router.get(
    "/{message_id}/masterrecords",
    response_model=list[MasterRecordSchema],
    dependencies=[
        Security(auth.permission([Permissions.READ_MESSAGES, Permissions.READ_RECORDS]))
    ],
)
async def message_masterrecords(
    message_obj: Message = Depends(_get_message),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive MasterRecords associated with a specific error message"""
    # Get masterrecords directly referenced by the error
    records = jtrace.query(MasterRecord).filter(
        MasterRecord.nationalid == message_obj.ni
    )

    # Apply permissions
    records = apply_masterrecord_list_permissions(records, user)

    # Add audit events
    message_audit = audit.add_event(
        Resource.MESSAGE, message_obj.id, MessageOperation.READ
    )
    for record in records:
        audit.add_event(
            Resource.MASTER_RECORD,
            record.id,
            AuditOperation.READ,
            parent=message_audit,
        )

    return records.all()

import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.exceptions import HTTPException
from mirth_client.mirth import MirthAPI
from mirth_client.models import ConnectorMessageData, ConnectorMessageModel
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    MessageOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.messages import ERROR_SORTER, get_message, get_messages
from ukrdc_fastapi.query.workitems import get_workitems_related_to_message
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, WorkItemSchema
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter

router = APIRouter(tags=["Messages"])


class MessageSourceSchema(OrmModel):
    content: Optional[str]
    content_type: Optional[str]


@router.get(
    "/",
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
    audit.add_event(Resource.MESSAGES, None, MessageOperation.READ)
    return paginate(
        sorter.sort(
            get_messages(
                errorsdb,
                user,
                statuses=status,
                nis=ni,
                facility=facility,
                since=since,
                until=until,
            )
        )
    )


@router.get(
    "/{message_id}/",
    response_model=MessageSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
def message(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive detailed information about a specific error message"""
    # For some reason the fastAPI response_model doesn't call our channel_name
    # validator, meaning we don't get a populated channel name unless we explicitly
    # call it here.
    message_obj = get_message(errorsdb, message_id, user)
    audit.add_event(Resource.MESSAGE, message_obj.id, MessageOperation.READ)
    return MessageSchema.from_orm(message_obj)


@router.get(
    "/{message_id}/source",
    response_model=MessageSourceSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
async def message_source(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive detailed information about a specific error message"""
    error = get_message(errorsdb, message_id, user)

    if not error.channel_id:
        raise HTTPException(404, "Channel ID not found in Mirth")

    message_obj = await mirth.channel(error.channel_id).get_message(
        str(error.message_id), include_content=True
    )
    if not message_obj:
        raise HTTPException(404, "Message not found in Mirth")

    first_connector_message: ConnectorMessageModel = list(
        message_obj.connector_messages.values()
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

    audit.add_event(Resource.MESSAGE, error.id, MessageOperation.READ_SOURCE)

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
    message_id: str,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive WorkItems associated with a specific error message"""
    message_obj = get_message(errorsdb, message_id, user)

    workitems = get_workitems_related_to_message(
        jtrace, errorsdb, str(message_obj.id), user
    ).all()

    message_audit = audit.add_event(
        Resource.MESSAGE, message_obj.id, MessageOperation.READ
    )
    for item in workitems:
        audit.add_workitem(item, parent=message_audit)

    return workitems


@router.get(
    "/{message_id}/masterrecords",
    response_model=list[MasterRecordSchema],
    dependencies=[
        Security(auth.permission([Permissions.READ_MESSAGES, Permissions.READ_RECORDS]))
    ],
)
async def message_masterrecords(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user()),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive MasterRecords associated with a specific error message"""
    message_obj = get_message(errorsdb, message_id, user)

    # Get masterrecords directly referenced by the error
    records = (
        jtrace.query(MasterRecord)
        .filter(MasterRecord.nationalid == message_obj.ni)
        .all()
    )

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

    return records

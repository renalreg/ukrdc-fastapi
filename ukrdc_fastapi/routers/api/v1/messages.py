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
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.messages import ERROR_SORTER, get_message, get_messages
from ukrdc_fastapi.query.workitems import get_workitems_related_to_message
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, WorkItemShortSchema
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import Sorter

router = APIRouter(tags=["Messages"])


class MessageSourceSchema(OrmModel):
    content: Optional[str]
    content_type: Optional[str]


@router.get(
    "/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_messages(
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[str] = None,
    ni: Optional[list[str]] = QueryParam([]),
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    sorter: Sorter = Depends(ERROR_SORTER),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    query = get_messages(
        errorsdb,
        user,
        status=status,
        nis=ni,
        facility=facility,
        since=since,
        until=until,
    )
    return paginate(sorter.sort(query))


@router.get(
    "/{message_id}/",
    response_model=MessageSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_detail(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Retreive detailed information about a specific error message"""
    return get_message(errorsdb, message_id, user)


@router.get(
    "/{message_id}/source",
    response_model=MessageSourceSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
async def error_source(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    mirth: MirthAPI = Depends(get_mirth),
):
    """Retreive detailed information about a specific error message"""
    error = get_message(errorsdb, message_id, user)

    if not error.channel_id:
        raise HTTPException(404, "Channel ID not found")

    message = await mirth.channel(error.channel_id).get_message(
        str(error.message_id), include_content=True
    )
    if not message:
        raise HTTPException(404, "Mirth message not found")

    first_connector_message: ConnectorMessageModel = list(
        message.connector_messages.values()
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

    return MessageSourceSchema(
        content=message_data.content, content_type=message_data.data_type
    )


@router.get(
    "/{message_id}/workitems",
    response_model=list[WorkItemShortSchema],
    dependencies=[
        Security(
            auth.permission(
                [auth.permissions.READ_ERRORS, auth.permissions.READ_WORKITEMS]
            )
        )
    ],
)
async def error_workitems(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive WorkItems associated with a specific error message"""
    return get_workitems_related_to_message(jtrace, errorsdb, message_id, user).all()


@router.get(
    "/{message_id}/masterrecords",
    response_model=list[MasterRecordSchema],
    dependencies=[
        Security(
            auth.permission(
                [auth.permissions.READ_ERRORS, auth.permissions.READ_RECORDS]
            )
        )
    ],
)
async def error_masterrecords(
    message_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive MasterRecords associated with a specific error message"""
    error = get_message(errorsdb, message_id, user)

    # Get masterrecords directly referenced by the error
    return jtrace.query(MasterRecord).filter(MasterRecord.nationalid == error.ni).all()

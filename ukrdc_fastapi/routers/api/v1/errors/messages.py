import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from fastapi.exceptions import HTTPException
from mirth_client.mirth import MirthAPI
from mirth_client.models import ConnectorMessageData, ConnectorMessageModel
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_mirth
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.errors import get_error, get_errors
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.errors import ExtendedErrorSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Errors/Messages"])


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
    status: str = "ERROR",
    ni: Optional[list[str]] = QueryParam([]),
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    return paginate(
        get_errors(
            errorsdb,
            user,
            status=status,
            nis=ni,
            facility=facility,
            since=since,
            until=until,
        )
    )


@router.get(
    "/{error_id}/",
    response_model=ExtendedErrorSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_detail(
    error_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive detailed information about a specific error message"""
    return get_error(errorsdb, jtrace, error_id, user)


@router.get(
    "/{error_id}/source",
    response_model=MessageSourceSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
async def error_source(
    error_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
):
    """Retreive detailed information about a specific error message"""
    # TODO: Run get_errors in threadpool
    error = get_error(errorsdb, jtrace, error_id, user)

    message = await mirth.channel(error.channel_id).get_message(
        str(error.message_id), include_content=True
    )
    if not message:
        raise HTTPException(404, "Mirth message not found")

    first_connector_message: ConnectorMessageModel = list(
        message.connector_messages.values()
    )[0]

    message_data: Optional[ConnectorMessageData]

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

import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.dependencies import get_errorsdb
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils import parse_date

router = APIRouter()


@router.get("/", response_model=Page[MessageSchema])
def error_messages(
    ni: Optional[str] = None,
    facility: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    status: Optional[str] = None,
    errorsdb: Session = Depends(get_errorsdb),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    """Retreive a list of error messages, optionally filtered by NI, facility, or date"""
    messages = errorsdb.query(Message)

    # Default to showing last 7 days
    since_datetime: datetime.datetime = parse_date(
        since
    ) or datetime.datetime.utcnow() - datetime.timedelta(days=7)
    messages = messages.filter(Message.received >= since_datetime)

    # Optionally filter out messages newer than `untildays`
    until_datetime: datetime.datetime = parse_date(until) or (
        datetime.datetime.utcnow()
    )
    messages = messages.filter(
        Message.received <= until_datetime + datetime.timedelta(days=1)
    )

    # Optionally filter by facility
    if facility:
        messages = messages.filter(Message.facility == facility)

    # Optionally filter by NI
    if ni:
        messages = messages.filter(Message.ni == ni)

    # Optionally filter by message status
    if status:
        messages = messages.filter(Message.msg_status == status)

    # Sort
    messages = messages.order_by(Message.received.desc())

    return paginate(messages)

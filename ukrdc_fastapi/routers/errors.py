import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb
from ukrdc_fastapi.models.errorsdb import Message
from ukrdc_fastapi.schemas.errors import MessageSchema

router = APIRouter()


@router.get("/", response_model=Page[MessageSchema])
def error_messages(
    ni: Optional[str] = None,
    facility: Optional[str] = None,
    fromdays: Optional[int] = None,
    untildays: Optional[int] = None,
    errorsdb: Session = Depends(get_errorsdb),
):
    messages = errorsdb.query(Message)

    # Default to showing last 7 days
    if not fromdays:
        fromdays = 7
    from_datetime: datetime.datetime = datetime.datetime.utcnow() - datetime.timedelta(
        days=fromdays
    )
    messages = messages.filter(Message.received > from_datetime)

    # Optionally filter out messages newer than `untildays`
    if untildays:
        until_datetime: datetime.datetime = (
            datetime.datetime.utcnow() - datetime.timedelta(days=untildays)
        )
        messages = messages.filter(Message.received <= until_datetime)

    # Optionally filter by facility
    if facility:
        messages = messages.filter(Message.facility == facility)

    # Optionally filter by NI
    if ni:
        messages = messages.filter(Message.ni == ni)

    return paginate(messages)

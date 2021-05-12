import datetime
from typing import Optional

from sqlalchemy.orm import Query
from ukrdc_sqla.errorsdb import Message


def filter_error_messages(
    query: Query,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[str] = None,
):
    """Filter an error message query by NI, facility, or date"""

    # Default to showing last 7 days
    since_datetime: datetime.datetime = (
        since or datetime.datetime.utcnow() - datetime.timedelta(days=7)
    )
    query = query.filter(Message.received >= since_datetime)

    # Optionally filter out messages newer than `untildays`
    if until:
        query = query.filter(Message.received <= until)

    # Optionally filter by facility
    if facility:
        query = query.filter(Message.facility == facility)

    # Optionally filter by message status
    if status:
        query = query.filter(Message.msg_status == status)

    # Sort
    query = query.order_by(Message.received.desc())

    return query

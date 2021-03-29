import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from .base import OrmModel


class ChannelSchema(OrmModel):
    id: str
    name: Optional[str]
    store_first_message: Optional[bool]
    store_last_message: Optional[bool]


class MessageSchema(OrmModel):
    id: str
    message_id: int
    channel_id: str
    received: Optional[datetime.datetime]
    msg_status: str
    ni: Optional[str]
    filename: Optional[str]
    facility: Optional[str]
    error: Optional[str]
    status: Optional[str]
    links = LinkSet(
        {
            "self": UrlFor(
                "mirth_channel_message",
                {"channel_id": "<channel_id>", "message_id": "<message_id>"},
            ),
        }
    )

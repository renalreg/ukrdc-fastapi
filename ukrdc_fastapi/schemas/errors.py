import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor
from pydantic import validator

from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.utils.mirth import get_channel_name

from .base import OrmModel


class ChannelSchema(OrmModel):
    id: str
    name: Optional[str]
    store_first_message: Optional[bool]
    store_last_message: Optional[bool]


class MinimalMessageSchema(OrmModel):
    id: int
    received: Optional[datetime.datetime]
    msg_status: str
    ni: Optional[str]
    filename: Optional[str]
    facility: Optional[str]


class MessageSchema(MinimalMessageSchema):
    message_id: int
    channel_id: str
    error: Optional[str]
    status: Optional[str]
    links = LinkSet(
        {
            "self": UrlFor(
                "error_detail",
                {"error_id": "<id>"},
            ),
            "source": UrlFor(
                "error_source",
                {"error_id": "<id>"},
            ),
            "mirth": UrlFor(
                "mirth_channel_message",
                {"channel_id": "<channel_id>", "message_id": "<message_id>"},
            ),
        }
    )

    channel: Optional[str]

    @validator("channel")
    def channel_name(cls, _, values):
        """
        Dynamically generates the channel name field
        by reading the Redis-cached channel info.
        """
        channel_id = values.get("channel_id")
        if channel_id:
            return get_channel_name(channel_id, get_redis())
        return None

import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor
from pydantic import validator

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
    error: Optional[str]
    status: Optional[str]
    links = LinkSet(
        {
            "self": UrlFor("error_detail", {"message_id": "<id>"}),
            "source": UrlFor("error_source", {"message_id": "<id>"}),
            "workitems": UrlFor("error_workitems", {"message_id": "<id>"}),
            "masterrecords": UrlFor("error_masterrecords", {"message_id": "<id>"}),
            "mirth": UrlFor(
                "mirth_channel_message",
                {"channel_id": "<channel_id>", "message_id": "<message_id>"},
            ),
        }
    )

    channel_id: str
    channel: Optional[str]

    _channel_id_name_map: dict[str, str]

    @classmethod
    def set_channel_id_name_map(cls, cinm: dict[str, str]):
        """
        Set the Mirth Channel ID-Name map.
        This model inserts a channel name from its channel_id field,
        when given a map of IDs to names.

        Args:
            cinm (dict[str, str]): Mirth Channel ID-Name map
        """
        cls._channel_id_name_map = cinm

    @validator("channel")
    def channel_name(cls, _, values):  # pylint: disable=no-self-argument,no-self-use
        """
        Dynamically generates the channel name field
        by reading the class Mirth Channel ID-Name map.
        """
        # TODO: Replace with computed_fields once available: https://github.com/samuelcolvin/pydantic/pull/2625
        if hasattr(cls, "_channel_id_name_map"):
            channel_id = values.get("channel_id")
            if channel_id:
                return cls._channel_id_name_map.get(channel_id)
        return None

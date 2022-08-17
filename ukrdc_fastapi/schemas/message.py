import datetime
from typing import Optional

from pydantic import Field, validator

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
    error: Optional[str]
    status: Optional[str]

    # Mirth message
    # Field names are determined by ORM, but we alias to something more useful for the API
    message_id: str = Field(alias="mirthMessageId")
    channel_id: str = Field(alias="mirthChannelId")
    mirth_channel: Optional[str]

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

    @validator("mirth_channel")
    def channel_name(cls, _, values):  # pylint: disable=no-self-argument
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

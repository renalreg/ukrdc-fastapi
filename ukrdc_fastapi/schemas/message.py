import datetime
from typing import Optional

from pydantic import Field, validator

from .base import OrmModel


class ChannelSchema(OrmModel):
    """Internal configuration information about a single Mirth channel"""

    id: str = Field(..., description="Channel ID")
    name: Optional[str] = Field(None, description="Channel name")
    store_first_message: Optional[bool] = Field(
        None, description="Is the first connector message of each message stored?"
    )
    store_last_message: Optional[bool] = Field(
        None, description="Is the last connector message of each message stored?"
    )


class MinimalMessageSchema(OrmModel):
    """A minimal representation of a single message"""

    id: int = Field(..., description="Message ID")
    received: Optional[datetime.datetime] = Field(
        None, description="Message received timestamp"
    )
    msg_status: str = Field(..., description="Message status code")
    ni: Optional[str] = Field(
        None, description="National ID of the patient the message is about"
    )
    filename: Optional[str] = Field(None, description="Filename of the message")
    facility: Optional[str] = Field(
        None, description="Facility code of the message sender"
    )


class MessageSchema(MinimalMessageSchema):
    """A full representation of a single message"""

    error: Optional[str] = Field(None, description="Error message, if any")
    status: Optional[str] = Field(None, description="Message status code")

    # Mirth message
    # Field names are determined by ORM, but we alias to something more useful for the API
    message_id: str = Field(alias="mirthMessageId", description="Mirth message ID")
    channel_id: str = Field(alias="mirthChannelId", description="Mirth channel ID")
    mirth_channel: Optional[str] = Field(
        None, description="Mirth channel name, if known"
    )

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

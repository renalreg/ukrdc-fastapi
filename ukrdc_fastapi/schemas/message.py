import datetime
from typing import ClassVar, Annotated

from pydantic import Field, field_validator, ValidationInfo, BeforeValidator

from .base import OrmModel


class ChannelSchema(OrmModel):
    """Internal configuration information about a single Mirth channel"""

    id: str = Field(..., description="Channel ID")
    name: str | None = Field(None, description="Channel name")
    store_first_message: bool | None = Field(
        None, description="Is the first connector message of each message stored?"
    )
    store_last_message: bool | None = Field(
        None, description="Is the last connector message of each message stored?"
    )


class MinimalMessageSchema(OrmModel):
    """A minimal representation of a single message"""

    id: int = Field(..., description="Message ID")
    received: datetime.datetime | None = Field(
        None, description="Message received timestamp"
    )
    msg_status: str = Field(..., description="Message status code")
    ni: str | None = Field(
        None, description="National ID of the patient the message is about"
    )
    filename: str | None = Field(None, description="Filename of the message")
    facility: str | None = Field(
        None, description="Facility code of the message sender"
    )


class MessageSchema(MinimalMessageSchema):
    """A full representation of a single message"""

    _channel_id_name_map: ClassVar[dict[str, str]] = {}

    error: str | None = Field(None, description="Error message, if any")
    status: str | None = Field(None, description="Message status code")

    # Mirth message
    # Field names are determined by ORM, but we alias to something more useful for the API
    message_id: Annotated[str, BeforeValidator(str)] = Field(
        alias="mirthMessageId", description="Mirth message ID"
    )
    channel_id: str = Field(alias="mirthChannelId", description="Mirth channel ID")
    mirth_channel: str | None = Field(None, description="Mirth channel name, if known")

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

    @field_validator("mirth_channel", mode="after")
    @classmethod
    def channel_name(cls, _, info: ValidationInfo):
        """
        Dynamically generates the channel name field
        by reading the class Mirth Channel ID-Name map.
        """
        # TODO: Replace with computed_fields once available: https://github.com/samuelcolvin/pydantic/pull/2625
        if cls._channel_id_name_map:
            channel_id = info.data.get("channel_id")
            if channel_id:
                return cls._channel_id_name_map.get(channel_id)
        return None

from fastapi_hypermodel import LinkSet, UrlFor
from mirth_client.models import ChannelMessageModel, ChannelModel

from .base import OrmModel


class MirthChannelModel(ChannelModel, OrmModel):
    links = LinkSet(
        {
            "self": UrlFor("mirth_channel", {"channel_id": "<id>"}),
        }
    )


class MirthChannelMessageModel(ChannelMessageModel, OrmModel):
    links = LinkSet(
        {
            "self": UrlFor(
                "mirth_channel_message",
                {"channel_id": "<channel_id>", "message_id": "<message_id>"},
            ),
        }
    )

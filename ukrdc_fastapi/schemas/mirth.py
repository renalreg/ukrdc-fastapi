from fastapi_hypermodel import LinkSet, UrlFor
from mirth_client.models import ChannelMessageModel, ChannelModel

from .base import OrmModel

"""
DEVELOPER NOTES:

We need to # type: ignore both these classes since MyPy dislikes the
differing Config class definitions in each base class. In practice this
works fine as Pydantic can handle this.
"""


class MirthChannelModel(ChannelModel, OrmModel):  # type: ignore
    links = LinkSet(
        {
            "self": UrlFor("mirth_channel", {"channel_id": "<id>"}),
        }
    )


class MirthChannelMessageModel(ChannelMessageModel, OrmModel):  # type: ignore
    links = LinkSet(
        {
            "self": UrlFor(
                "mirth_channel_message",
                {"channel_id": "<channel_id>", "message_id": "<message_id>"},
            ),
        }
    )

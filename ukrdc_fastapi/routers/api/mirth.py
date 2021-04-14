from fastapi import APIRouter, Depends
from mirth_client import Channel, MirthAPI

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.dependencies import get_mirth
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.mirth import MirthChannelMessageModel, MirthChannelModel

router = APIRouter()


class MirthPage(OrmModel):
    """Like a pagination Page but without a total"""

    page: int
    size: int


class MessagePage(MirthPage):
    items: list[MirthChannelMessageModel]


@router.get("/channels/", response_model=list[MirthChannelModel])
async def mirth_channels(
    mirth: MirthAPI = Depends(get_mirth),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    return await mirth.get_channels()


@router.get("/channels/{channel_id}/", response_model=MirthChannelModel)
async def mirth_channel(
    channel_id: str,
    mirth: MirthAPI = Depends(get_mirth),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    return await Channel(mirth, channel_id).get()


@router.get(
    "/channels/{channel_id}/messages/",
    response_model=MessagePage,
)
async def mirth_channel_messages(
    channel_id: str,
    page: int = 0,
    size: int = 20,
    mirth: MirthAPI = Depends(get_mirth),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    messages = await Channel(mirth, channel_id).get_messages(
        include_content=False, limit=size, offset=page * size
    )

    return {"page": page, "size": size, "items": messages}


@router.get(
    "/channels/{channel_id}/messages/{message_id}/",
    response_model=MirthChannelMessageModel,
)
async def mirth_channel_message(
    channel_id: str,
    message_id: int,
    mirth: MirthAPI = Depends(get_mirth),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    return await Channel(mirth, channel_id).get_message(
        message_id, include_content=True
    )

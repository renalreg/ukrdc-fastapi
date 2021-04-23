from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from mirth_client import MirthAPI
from redis import Redis

from ukrdc_fastapi.dependencies import get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Scopes, Security, User, auth
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.mirth import MirthChannelMessageModel
from ukrdc_fastapi.utils.mirth import (
    ChannelFullModel,
    ChannelGroupModel,
    get_cached_all,
    get_cached_channels_with_statistics,
)

router = APIRouter()


class MirthPage(OrmModel):
    """Like a pagination Page but without a total"""

    page: int
    size: int


class MessagePage(MirthPage):
    items: list[MirthChannelMessageModel]


@router.get("/channels/", response_model=list[ChannelFullModel])
async def mirth_channels(
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    return await get_cached_channels_with_statistics(mirth, redis)


@router.get("/groups/")
async def mirth_groups(
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
) -> list[ChannelGroupModel]:
    return await get_cached_all(mirth, redis)


@router.get("/channels/{channel_id}/", response_model=ChannelFullModel)
async def mirth_channel(
    channel_id: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    channels = await get_cached_channels_with_statistics(mirth, redis)
    channel_map = {str(channel.id): channel for channel in channels}

    channel: Optional[ChannelFullModel] = channel_map.get(channel_id)
    if not channel:
        raise HTTPException(404, detail="Channel not found")  # pragma: no cover

    return channel


@router.get(
    "/channels/{channel_id}/messages/",
    response_model=MessagePage,
)
async def mirth_channel_messages(
    channel_id: str,
    page: int = 0,
    size: int = 20,
    mirth: MirthAPI = Depends(get_mirth),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    messages = await mirth.channel(channel_id).get_messages(
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
    _: User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    return await mirth.channel(channel_id).get_message(message_id, include_content=True)

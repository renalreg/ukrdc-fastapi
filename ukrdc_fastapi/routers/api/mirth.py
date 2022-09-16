from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from mirth_client import MirthAPI
from mirth_client.models import ChannelMessageModel
from pydantic import Field
from redis import Redis

from ukrdc_fastapi.dependencies import get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.utils.mirth import (
    ChannelFullModel,
    ChannelGroupModel,
    get_channels_with_statistics,
    get_mirth_all,
)

router = APIRouter(tags=["Mirth"])


class MirthPage(OrmModel):
    """A pagination Page without a total"""

    page: int = Field(..., description="Page number")
    size: int = Field(..., description="Page size")


class MessagePage(MirthPage):
    items: list[ChannelMessageModel]


@router.get(
    "/channels",
    response_model=list[ChannelFullModel],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
async def mirth_channels(
    mirth: MirthAPI = Depends(get_mirth), redis: Redis = Depends(get_redis)
):
    """Retrieve a list of Mirth channels"""
    return await get_channels_with_statistics(mirth, redis)


@router.get(
    "/groups",
    response_model=list[ChannelGroupModel],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
async def mirth_groups(
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
) -> list[ChannelGroupModel]:
    """Retrieve a list of Mirth channel groups"""
    return await get_mirth_all(mirth, redis)


@router.get(
    "/channels/{channel_id}",
    response_model=ChannelFullModel,
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
async def mirth_channel(
    channel_id: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Get details and statistics about a specific Mirth channel"""
    channels = await get_channels_with_statistics(mirth, redis)
    channel_map = {str(channel.id): channel for channel in channels}

    channel: Optional[ChannelFullModel] = channel_map.get(channel_id)
    if not channel:
        raise HTTPException(404, detail="Channel not found")  # pragma: no cover

    return channel


@router.get(
    "/channels/{channel_id}/messages",
    response_model=MessagePage,
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
async def mirth_channel_messages(
    channel_id: str,
    page: int = 0,
    size: int = 20,
    mirth: MirthAPI = Depends(get_mirth),
):
    """Retreive a list a messages from a specific Mirth channel"""
    messages = await mirth.channel(channel_id).get_messages(
        include_content=False, limit=size, offset=page * size
    )

    return {"page": page, "size": size, "items": messages}


@router.get(
    "/channels/{channel_id}/messages/{message_id}",
    response_model=ChannelMessageModel,
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
async def mirth_channel_message(
    channel_id: str,
    message_id: str,
    mirth: MirthAPI = Depends(get_mirth),
):
    """Retreive a specific message from a specific Mirth channel"""
    message = await mirth.channel(channel_id).get_message(
        message_id, include_content=True
    )
    if not message:
        raise HTTPException(404, detail="Message not found in Mirth")
    return message

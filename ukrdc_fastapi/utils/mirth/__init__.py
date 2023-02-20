import asyncio
from typing import Optional
from uuid import UUID

from mirth_client import Channel, MirthAPI
from mirth_client.models import ChannelGroup, ChannelModel, ChannelStatistics
from pydantic import BaseModel, Field
from redis import Redis

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.utils.cache import BasicCache, CacheKey


class MirthMessageResponseSchema(BaseModel):
    """Response schema for Mirth message post views"""

    status: str = Field(..., description="Response status of the message")
    message: str = Field(..., description="Submitted message content")


class ChannelFullModel(OrmModel):
    """Full Mirth channel information, including statistics"""

    id: UUID = Field(..., description="Mirth channel ID")
    name: str = Field(..., description="Mirth channel name")
    description: Optional[str] = Field(None, description="Mirth channel description")
    revision: str = Field(..., description="Mirth channel revision")

    statistics: Optional[ChannelStatistics] = Field(
        None, description="Mirth channel statistics"
    )


class ChannelGroupModel(OrmModel):
    """Mirth channel group information"""

    id: UUID = Field(..., description="Mirth channel group ID")
    name: str = Field(..., description="Mirth channel group name")
    description: Optional[str] = Field(
        None, description="Mirth channel group description"
    )
    revision: str = Field(..., description="Mirth channel group revision")

    channels: list[ChannelFullModel] = Field(
        ..., description="Mirth channels in this group"
    )


async def get_channels(mirth: MirthAPI, redis: Redis) -> list[ChannelModel]:
    """Get a list of Mirth channel info

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelModel]: List of channel infos
    """
    cache = BasicCache(redis, CacheKey.MIRTH_CHANNEL_INFO)

    if not cache.exists:
        channel_info: list[ChannelModel] = await mirth.channel_info()
        cache.set(channel_info, expire=settings.cache_mirth_channel_seconds)

    return [ChannelModel(**channel) for channel in cache.get()]


async def get_groups(mirth: MirthAPI, redis: Redis) -> list[ChannelGroup]:
    """Get a list of Mirth channel groups

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelGroup]: List of channel groups
    """
    cache = BasicCache(redis, CacheKey.MIRTH_GROUPS)

    if not cache.exists:
        groups: list[ChannelGroup] = await mirth.groups()
        cache.set(groups, expire=settings.cache_mirth_groups_seconds)

    return [ChannelGroup(**group) for group in cache.get()]


async def get_statistics(mirth: MirthAPI, redis: Redis) -> list[ChannelStatistics]:
    """Get a list of Mirth channel statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelStatistics]: List of channel statistics
    """
    cache = BasicCache(redis, CacheKey.MIRTH_STATISTICS)

    if not cache.exists:
        statistics: list[ChannelStatistics] = await mirth.statistics()
        cache.set(statistics, expire=settings.cache_mirth_statistics_seconds)

    return [ChannelStatistics(**stat) for stat in cache.get()]


async def get_channels_with_statistics(
    mirth: MirthAPI, redis: Redis
) -> list[ChannelFullModel]:
    """Get a list of Mirth channel info, including statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelFullModel]: List of channel infos including statistics
    """
    channels: list[ChannelModel]
    statistics: list[ChannelStatistics]

    channels, statistics = await asyncio.gather(
        get_channels(mirth, redis), get_statistics(mirth, redis)
    )

    statistics_map: dict[str, ChannelStatistics] = {
        str(stats.channel_id): stats for stats in statistics
    }

    return sorted(
        [
            ChannelFullModel(
                id=channel.id,
                name=channel.name,
                description=channel.description,
                revision=channel.revision,
                statistics=statistics_map.get(
                    str(channel.id),
                ),
            )
            for channel in channels
        ],
        key=lambda channel: channel.name,
    )


async def get_mirth_all(mirth: MirthAPI, redis: Redis) -> list[ChannelGroupModel]:
    """Get a list of Mirth channel groups,
    including full channel info with statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelGroupModel]: List of channel groups
    """
    channels: list[ChannelFullModel]
    groups: list[ChannelGroup]

    channels, groups = await asyncio.gather(
        get_channels_with_statistics(mirth, redis), get_groups(mirth, redis)
    )

    channel_with_statistics_map: dict[UUID, ChannelFullModel] = {
        channel.id: channel for channel in channels
    }

    groups_with_statistics: list[ChannelGroupModel] = [
        ChannelGroupModel(
            id=group.id,
            name=group.name,
            description=group.description,
            revision=group.revision,
            channels=[
                channel_with_statistics_map[channel.id]
                for channel in group.channels
                if channel.id in channel_with_statistics_map
            ],
        )
        for group in groups
    ]

    # Sort the groups by name
    groups_with_statistics.sort(key=lambda group: group.name)

    # The Mirth API unhelpfully doesn't include the [Default Group] group in its
    # groups API response, so we have to build it ourselves. We first find all channels
    # that are already in a group, and use that to find any channels NOT in a group, which
    # corresponds to the [Default Group] group. Group.
    channel_ids_in_groups: set[UUID] = {
        channel.id for group in groups for channel in group.channels
    }
    channels_not_in_groups: list[ChannelFullModel] = [
        channel for channel in channels if channel.id not in channel_ids_in_groups
    ]
    groups_with_statistics.insert(
        0,
        ChannelGroupModel(
            id=UUID("00000000-00000000-00000000-00000000"),
            name="Default Group",
            description="Channels not part of a group will appear here",
            revision="--",
            channels=[
                channel_with_statistics_map[channel.id]
                for channel in channels_not_in_groups
                if channel.id in channel_with_statistics_map
            ],
        ),
    )

    # Sort channels within groups by name
    for group in groups_with_statistics:
        group.channels.sort(key=lambda channel: channel.name)

    return groups_with_statistics


async def get_channel_map(
    mirth: MirthAPI, redis: Redis, by_name: bool = False
) -> dict[str, ChannelModel]:
    """Fetch a mapping of channel IDs -> ChannelModel objects.
    To reduce load on the Mirth server, channel mappings will
    be cached to Redis, and reloaded only when required.

    Args:
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis instance for map caching
        by_name (bool, optional): Use channel name as the returned keys. Defaults to False.

    Returns:
        dict[str, ChannelModel]: Mapping of channel ID or name to ChannelModel objects
    """
    channels: list[ChannelModel] = await get_channels(mirth, redis)

    channel_map: dict[str, ChannelModel] = {
        str(channel.id): channel for channel in channels
    }
    if not by_name:
        return channel_map
    return {channel.name: channel for channel in channel_map.values()}


async def get_channel_from_name(
    name: str, mirth: MirthAPI, redis: Redis
) -> Optional[Channel]:
    """Find a Mirth channel by channel name, and return an interactive
    Channel object if a match is found.

    Args:
        name (str): Channel name string
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis instance for map caching

    Returns:
        Optional[Channel]: Interactive Channel object, if a match is found.
    """
    name_map: dict[str, ChannelModel] = await get_channel_map(
        mirth, redis, by_name=True
    )
    if name not in name_map:
        return None

    return mirth.channel(name_map[name].id)


async def get_channel_name(id_: str, mirth: MirthAPI, redis: Redis) -> Optional[str]:
    """Get a channels name from its UUID

    Args:
        id_ (str): Channel ID
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis instance for map caching

    Returns:
        Optional[str]: Channel name
    """
    id_map: dict[str, ChannelModel] = await get_channel_map(mirth, redis)
    channel: Optional[ChannelModel] = id_map.get(id_)
    if channel:
        return channel.name
    return None

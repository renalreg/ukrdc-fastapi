import asyncio
from typing import Optional
from uuid import UUID

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from mirth_client import Channel, MirthAPI
from mirth_client.models import ChannelGroup, ChannelModel, ChannelStatistics
from pydantic import BaseModel
from redis import Redis

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.schemas.base import OrmModel


class MirthMessageResponseSchema(BaseModel):
    """Response schema for Mirth message post views"""

    status: str
    message: str


class ChannelStatisticsSimplifiedModel(OrmModel):
    received: int
    sent: int
    error: int
    filtered: int
    queued: int


class ChannelFullModel(OrmModel):
    id: UUID
    name: str
    description: Optional[str]
    revision: str

    statistics: Optional[ChannelStatisticsSimplifiedModel]


class ChannelGroupModel(OrmModel):
    id: UUID
    name: str
    description: Optional[str]
    revision: str

    channels: list[ChannelFullModel]


async def get_cached_channels(mirth: MirthAPI, redis: Redis) -> list[ChannelModel]:
    """Get a cached (if available) list of Mirth channel info

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelModel]: List of channel infos
    """
    redis_key: str = "mirth:channel_info"
    channel_info: list[ChannelModel]

    if not redis.exists(redis_key):
        channel_info = await mirth.channel_info()
        redis.hset(  # type: ignore
            redis_key,
            mapping={
                str(channel.id): channel.json(by_alias=True) for channel in channel_info
            },
        )
        redis.expire(redis_key, settings.cache_channel_seconds)
    else:
        channel_info_json: dict[str, str] = redis.hgetall(redis_key)

        channel_info = [
            ChannelModel.parse_raw(channel) for channel in channel_info_json.values()
        ]

    return channel_info


async def get_cached_groups(mirth: MirthAPI, redis: Redis) -> list[ChannelGroup]:
    """Get a cached (if available) list of Mirth channel groups

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelGroup]: List of channel groups
    """
    redis_key: str = "mirth:groups"
    groups: list[ChannelGroup]

    if not redis.exists(redis_key):
        groups = await mirth.groups()
        redis.hset(  # type: ignore
            redis_key,
            mapping={str(group.id): group.json(by_alias=True) for group in groups},
        )
        redis.expire(redis_key, settings.cache_groups_seconds)
    else:
        groups_json: dict[str, str] = redis.hgetall(redis_key)

        groups = [ChannelGroup.parse_raw(group) for group in groups_json.values()]

    return groups


async def get_cached_statistics(
    mirth: MirthAPI, redis: Redis
) -> list[ChannelStatistics]:
    """Get a cached (if available) list of Mirth channel statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelStatistics]: List of channel statistics
    """
    redis_key: str = "mirth:statistics"
    statistics: list[ChannelStatistics]

    if not redis.exists(redis_key):
        statistics = await mirth.statistics()
        redis.hset(  # type: ignore
            redis_key,
            mapping={
                str(stat.channel_id): stat.json(by_alias=True) for stat in statistics
            },
        )
        redis.expire(redis_key, settings.cache_statistics_seconds)
    else:
        statistics_json: dict[str, str] = redis.hgetall(redis_key)

        statistics = [
            ChannelStatistics.parse_raw(stat) for stat in statistics_json.values()
        ]

    return statistics


async def get_cached_channels_with_statistics(
    mirth: MirthAPI, redis: Redis
) -> list[ChannelFullModel]:
    """Get a cached (if available) list of Mirth channel info, including statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelFullModel]: List of channel infos including statistics
    """
    channels, statistics = await asyncio.gather(
        get_cached_channels(mirth, redis),
        get_cached_statistics(mirth, redis),
    )
    statistics_map: dict[str, ChannelStatistics] = {
        stats.channel_id: stats for stats in statistics
    }

    return [
        ChannelFullModel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            revision=channel.revision,
            statistics=statistics_map.get(channel.id),
        )
        for channel in channels
    ]


async def get_cached_all(mirth: MirthAPI, redis: Redis) -> list[ChannelGroupModel]:
    """Get a cached (if available) list of Mirth channel groups,
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
        get_cached_channels_with_statistics(mirth, redis),
        get_cached_groups(mirth, redis),
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
                channel_with_statistics_map.get(channel.id)
                for channel in group.channels
                if channel.id in channel_with_statistics_map
            ],
        )
        for group in groups
    ]

    return groups_with_statistics


async def get_cached_channel_map(
    mirth: MirthAPI, redis: Redis, by_name: bool = False
) -> dict[str, ChannelFullModel]:
    """Fetch a mapping of channel IDs -> ChannelModel objects.
    To reduce load on the Mirth server, channel mappings will
    be cached to Redis, and reloaded only when required.

    Args:
        mirth (MirthAPI): Mirth API instance
        redis (Redis): Redis instance for map caching
        by_name (bool, optional): Use channel name as the returned keys. Defaults to False.

    Returns:
        dict[str, ChannelFullModel]: Mapping of channel ID or name to ChannelFullModel objects
    """
    channels: list[ChannelModel] = await get_cached_channels(mirth, redis)

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
    name_map: dict[str, ChannelModel] = await get_cached_channel_map(
        mirth, redis, by_name=True
    )
    if name not in name_map:
        return None

    return mirth.channel(name_map[name].id)


def build_merge_message(superceding: str, superceeded: str) -> str:
    """Build rawData for two master records be merged.

    Args:
        superceding (str): MasterRecord.id of first item in merge
        superceeded (str): MasterRecord.id of second item in merge

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    superceding_element = SubElement(root, "superceding")
    superceding_element.text = str(superceding)

    superceeded_element = SubElement(root, "superceeded")
    superceeded_element.text = str(superceeded)

    return tostring(root, encoding="unicode")


def build_unlink_message(
    master_record: str,
    person_id: str,
    user: str,
    description: Optional[str] = None,
) -> str:
    """Build rawData for a Person record be unlinked from a MasterRecord

    Args:
        master_record (str): MasterRecord.id
        person_id (str): Person.id
        user (str): End user initiating the unlink
        description (Optional[str], optional): Unlink comments. Defaults to None.

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    mr_element = SubElement(root, "masterRecord")
    mr_element.text = str(master_record)

    id_element = SubElement(root, "personId")
    id_element.text = str(person_id)

    ud_element = SubElement(root, "updateDescription")
    ud_element.text = str(description or "")

    ub_element = SubElement(root, "updatedBy")
    ub_element.text = str(user)[:20]

    return tostring(root, encoding="unicode")


def build_update_workitem_message(
    workitem_id: int, status: int, description: Optional[str], user: str
) -> str:
    """Build rawData to update a WorkItem record

    Args:
        workitem_id (int): WorkItem.id to update
        status (int): New WorkItem.status
        description (Optional[str]): Update comments
        user (str): End user initiating the update

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    wi_element = SubElement(root, "workitem")
    wi_element.text = str(workitem_id)

    st_element = SubElement(root, "status")
    st_element.text = str(status)

    ud_element = SubElement(root, "updateDescription")
    ud_element.text = str(description or "")[:100]

    ub_element = SubElement(root, "updatedBy")
    ub_element.text = str(user)[:20]

    return tostring(root, encoding="unicode")


def build_close_workitem_message(workitem_id: int, description: str, user: str) -> str:
    """Build rawData to close a WorkItem without merging

    Args:
        workitem_id (int): WorkItem.id to close
        description (str): Comments on WorkItem close
        user (str): End user initiating the close

    Returns:
        str: XML rawData for Mirth message
    """
    return build_update_workitem_message(workitem_id, 3, description, user)


def build_export_tests_message(pid: str) -> str:
    """Build rawData to export PatientRecord test results to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = str(pid)

    tst_element = SubElement(root, "tests")
    tst_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_docs_message(pid: str) -> str:
    """Build rawData to export PatientRecord documents to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = str(pid)

    doc_element = SubElement(root, "documents")
    doc_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_all_message(pid: str) -> str:
    """Buold rawData to export PatientRecord test results and documents to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = str(pid)

    tst_element = SubElement(root, "tests")
    tst_element.text = "FULL"

    doc_element = SubElement(root, "documents")
    doc_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_radar_message(pid: str) -> str:
    """Build rawData to export a PatientRecord to RaDaR

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = str(pid)

    return tostring(root, encoding="unicode")

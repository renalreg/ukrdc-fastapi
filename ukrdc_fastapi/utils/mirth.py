from typing import Optional
from uuid import UUID

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from mirth_client import Channel, MirthAPI
from mirth_client.models import ChannelGroup, ChannelModel, ChannelStatistics
from pydantic import BaseModel
from redis import Redis

from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.message import MessageSchema


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


async def cache_channel_info(mirth: MirthAPI, redis: Redis) -> list[ChannelModel]:
    """Cache (to Redis) the list of Mirth channel infos

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelModel]: List of channel infos
    """
    redis_key: str = "mirth:channel_info"
    channel_info: list[ChannelModel] = await mirth.channel_info()
    redis.hset(  # type: ignore
        redis_key,
        mapping={
            str(channel.id): channel.json(by_alias=True) for channel in channel_info
        },
    )

    # Some of our models need the ID-name map to function properly
    id_name_map = {str(channel.id): channel.name for channel in channel_info}
    MessageSchema.set_channel_id_name_map(id_name_map)

    return channel_info


async def cache_channel_groups(mirth: MirthAPI, redis: Redis) -> list[ChannelGroup]:
    """Cache (to Redis) the list of Mirth channel groups

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelGroup]: List of channel groups
    """
    redis_key: str = "mirth:groups"

    groups: list[ChannelGroup] = await mirth.groups()
    redis.hset(  # type: ignore
        redis_key,
        mapping={str(group.id): group.json(by_alias=True) for group in groups},
    )

    return groups


async def cache_channel_statistics(
    mirth: MirthAPI, redis: Redis
) -> list[ChannelStatistics]:
    """Cache (to redis) the list of Mirth channel statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelStatistics]: List of channel statistics
    """
    redis_key: str = "mirth:statistics"

    statistics: list[ChannelStatistics] = await mirth.statistics()
    redis.hset(  # type: ignore
        redis_key,
        mapping={str(stat.channel_id): stat.json(by_alias=True) for stat in statistics},
    )

    return statistics


def get_cached_channels(redis: Redis) -> list[ChannelModel]:
    """Get a list of Mirth channel info

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelModel]: List of channel infos
    """
    redis_key: str = "mirth:channel_info"
    channel_info: list[ChannelModel]

    channel_info_json: dict[str, str] = redis.hgetall(redis_key)
    channel_info = [
        ChannelModel.parse_raw(channel) for channel in channel_info_json.values()
    ]

    return channel_info


def get_cached_groups(redis: Redis) -> list[ChannelGroup]:
    """Get a list of Mirth channel groups

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelGroup]: List of channel groups
    """
    redis_key: str = "mirth:groups"
    groups: list[ChannelGroup]

    groups_json: dict[str, str] = redis.hgetall(redis_key)
    groups = [ChannelGroup.parse_raw(group) for group in groups_json.values()]

    return groups


def get_cached_statistics(redis: Redis) -> list[ChannelStatistics]:
    """Get a list of Mirth channel statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelStatistics]: List of channel statistics
    """
    redis_key: str = "mirth:statistics"
    statistics: list[ChannelStatistics]

    statistics_json: dict[str, str] = redis.hgetall(redis_key)
    statistics = [
        ChannelStatistics.parse_raw(stat) for stat in statistics_json.values()
    ]

    return statistics


def get_cached_channels_with_statistics(redis: Redis) -> list[ChannelFullModel]:
    """Get a list of Mirth channel info, including statistics

    Args:
        mirth (MirthAPI): API instance
        redis (Redis): Redis cache instance

    Returns:
        list[ChannelFullModel]: List of channel infos including statistics
    """
    channels, statistics = (
        get_cached_channels(redis),
        get_cached_statistics(redis),
    )
    statistics_map: dict[str, ChannelStatistics] = {
        str(stats.channel_id): stats for stats in statistics
    }

    return [
        ChannelFullModel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            revision=channel.revision,
            statistics=statistics_map.get(str(channel.id)),
        )
        for channel in channels
    ]


def get_cached_all(redis: Redis) -> list[ChannelGroupModel]:
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
    channels, groups = (
        get_cached_channels_with_statistics(redis),
        get_cached_groups(redis),
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
    groups_with_statistics.append(
        ChannelGroupModel(
            id="00000000-00000000-00000000-00000000",
            name="Default Group",
            description="Channels not part of a group will appear here",
            revision="--",
            channels=[
                channel_with_statistics_map.get(channel.id)
                for channel in channels_not_in_groups
                if channel.id in channel_with_statistics_map
            ],
        )
    )

    return groups_with_statistics


def get_cached_channel_map(
    redis: Redis, by_name: bool = False
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
    channels: list[ChannelModel] = get_cached_channels(redis)

    channel_map: dict[str, ChannelModel] = {
        str(channel.id): channel for channel in channels
    }
    if not by_name:
        return channel_map
    return {channel.name: channel for channel in channel_map.values()}


def get_channel_from_name(
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
    name_map: dict[str, ChannelModel] = get_cached_channel_map(redis, by_name=True)
    if name not in name_map:
        return None

    return mirth.channel(name_map[name].id)


def get_channel_name(id_: str, redis: Redis) -> Optional[str]:
    """Get a channels name from its UUID

    Args:
        id_ (str): Channel ID
        redis (Redis): Redis instance for map caching

    Returns:
        Optional[str]: Channel name
    """
    id_map: dict[str, ChannelModel] = get_cached_channel_map(redis)
    channel: Optional[ChannelModel] = id_map.get(id_, None)
    if channel:
        return channel.name
    return None


def build_merge_message(superseding: int, superseded: int) -> str:
    """Build rawData for two master records be merged.
    Note: Superseded and superseding are spelt wrong in the
    Mirth messages. This is known.

    Args:
        superseding (int): MasterRecord.id of first item in merge
        superseded (int): MasterRecord.id of second item in merge

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    superceding_element = SubElement(root, "superceding")
    superceding_element.text = str(superseding)

    superceeded_element = SubElement(root, "superceeded")
    superceeded_element.text = str(superseded)

    return tostring(root, encoding="unicode")


def build_unlink_message(
    master_record: int,
    person_id: int,
    user: str,
    description: Optional[str] = None,
) -> str:
    """Build rawData for a Person record be unlinked from a MasterRecord

    Args:
        master_record (int): MasterRecord.id
        person_id (int): Person.id
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

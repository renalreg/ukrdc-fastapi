from fastapi_utils.tasks import repeat_every
from ukrdc_sqla.ukrdc import Facility

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis, get_root_task_tracker
from ukrdc_fastapi.dependencies.database import errors_session, ukrdc3_session
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.query.facilities import build_facilities_list
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.cache import BasicCache, CacheKey
from ukrdc_fastapi.utils.mirth import get_channel_map


@repeat_every(seconds=settings.cache_mirth_channel_seconds)
async def update_channel_id_name_map() -> None:
    """
    Update the in-memory Mirth Channel ID-Name map used by MessageSchema
    to populate the channel_name field from the channel_id field.

    Repeats every `cache_mirth_channel_seconds` seconds, to match the cache expiry time.

    The function runs as a tracked background task.
    """

    async def func():
        async with mirth_session() as mirth:
            id_channel_map = await get_channel_map(mirth, get_redis())

            id_name_map = {key: channel.name for key, channel in id_channel_map.items()}
            MessageSchema.set_channel_id_name_map(id_name_map)

    task = get_root_task_tracker().create(
        func, name="Update MessageSchema Mirth Channel ID-Name map"
    )
    return await task.tracked()


@repeat_every(seconds=settings.cache_facilities_list_seconds)
async def update_facilities_list() -> None:
    """
    Update the cached info and basic counts for all facilities.

    Repeats every `cache_facilities_list_seconds` seconds, to match the cache expiry time.

    The function runs as a tracked background task.
    """

    async def func():
        with ukrdc3_session() as ukrdc3, errors_session() as errorsdb:
            BasicCache(get_redis(), CacheKey.FACILITIES_LIST).set(
                build_facilities_list(ukrdc3.query(Facility), ukrdc3, errorsdb),
                expire=settings.cache_facilities_list_seconds,
            )

    task = get_root_task_tracker().create(func, name="Update root Facilities cache")
    return await task.tracked()

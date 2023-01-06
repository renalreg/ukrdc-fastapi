from fastapi_utils.tasks import repeat_every

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis, get_root_task_tracker
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.schemas.message import MessageSchema
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
            cache_redis = get_redis()
            id_channel_map = await get_channel_map(mirth, cache_redis)

            id_name_map = {key: channel.name for key, channel in id_channel_map.items()}
            MessageSchema.set_channel_id_name_map(id_name_map)

    task = get_root_task_tracker().create(
        func, name="Update MessageSchema Mirth Channel ID-Name map"
    )
    return await task.tracked()

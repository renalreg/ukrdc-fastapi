import logging

from fastapi_utils.tasks import repeat_every

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis, get_root_task_tracker
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.utils.mirth import (
    cache_channel_groups,
    cache_channel_info,
    cache_channel_statistics,
)


@repeat_every(seconds=settings.cache_channel_seconds)
async def cache_mirth_channel_info() -> None:
    """FastAPI Utils task to refresh Mirth channel info"""

    async def func():
        async with mirth_session() as mirth:
            await mirth.login(settings.mirth_user, settings.mirth_pass)
            cache_redis = get_redis()
            logging.info("Refreshing Mirth channel infos")
            await cache_channel_info(mirth, cache_redis)

    task = get_root_task_tracker().create(func, name="Cache Mirth channel info")
    return await task.tracked()


@repeat_every(seconds=settings.cache_groups_seconds)
async def cache_mirth_channel_groups() -> None:
    """FastAPI Utils task to refresh Mirth channel groups"""

    async def func():
        async with mirth_session() as mirth:
            await mirth.login(settings.mirth_user, settings.mirth_pass)
            cache_redis = get_redis()
            logging.info("Refreshing Mirth channel groups")
            await cache_channel_groups(mirth, cache_redis)

    task = get_root_task_tracker().create(func, name="Cache Mirth channel groups")
    return await task.tracked()


@repeat_every(seconds=settings.cache_statistics_seconds)
async def cache_mirth_channel_statistics() -> None:
    """FastAPI Utils task to refresh Mirth channel statistics"""

    async def func():
        async with mirth_session() as mirth:
            await mirth.login(settings.mirth_user, settings.mirth_pass)
            cache_redis = get_redis()
            logging.info("Refreshing Mirth channel statistics")
            await cache_channel_statistics(mirth, cache_redis)

    task = get_root_task_tracker().create(func, name="Cache Mirth channel statistics")
    return await task.tracked()

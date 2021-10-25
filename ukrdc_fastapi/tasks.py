import logging

from fastapi_utils.tasks import repeat_every

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.database import jtrace_session
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.query.dashboard import get_empi_stats, get_workitems_stats
from ukrdc_fastapi.utils.mirth import (
    cache_channel_groups,
    cache_channel_info,
    cache_channel_statistics,
)


@repeat_every(seconds=settings.cache_dashboard_seconds)
def cache_dash_stats() -> None:
    """FastAPI Utils task to refresh statistics for the admin dashboard"""
    with jtrace_session() as jtrace:
        redis = get_redis()
        logging.info("Refreshing admin statistics")
        get_workitems_stats(jtrace, redis, refresh=True)
        get_empi_stats(jtrace, redis, refresh=True)


@repeat_every(seconds=settings.cache_channel_seconds)
async def cache_mirth_channel_info() -> None:
    """FastAPI Utils task to refresh Mirth channel info"""
    async with mirth_session() as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel infos")
        await cache_channel_info(mirth, redis)


@repeat_every(seconds=settings.cache_groups_seconds)
async def cache_mirth_channel_groups() -> None:
    """FastAPI Utils task to refresh Mirth channel groups"""
    async with mirth_session() as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel groups")
        await cache_channel_groups(mirth, redis)


@repeat_every(seconds=settings.cache_statistics_seconds)
async def cache_mirth_channel_statistics() -> None:
    """FastAPI Utils task to refresh Mirth channel statistics"""
    async with mirth_session() as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel statistics")
        await cache_channel_statistics(mirth, redis)

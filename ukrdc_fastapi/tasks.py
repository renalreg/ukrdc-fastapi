import logging

from fastapi_utils.tasks import repeat_every
from mirth_client.mirth import MirthAPI
from ukrdc_sqla.ukrdc import Code

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.database import (
    ErrorsSession,
    JtraceSession,
    Ukrdc3Session,
)
from ukrdc_fastapi.query.dashboard import get_empi_stats, get_workitems_stats
from ukrdc_fastapi.query.facilities import (
    _get_and_cache_errors_history,
    _get_and_cache_facility,
)
from ukrdc_fastapi.utils.mirth import (
    cache_channel_groups,
    cache_channel_info,
    cache_channel_statistics,
)


@repeat_every(seconds=settings.cache_statistics_seconds)
def cache_all_facilities() -> None:
    """FastAPI Utils task to refresh statistics for each facility"""
    ukrdc3 = Ukrdc3Session()
    errorsdb = ErrorsSession()
    redis = get_redis()
    logging.info("Refreshing facility statistics")
    codes = ukrdc3.query(Code).filter(Code.coding_standard == "RR1+").all()
    for code in codes:
        logging.debug("Caching %s", code.code)
        _get_and_cache_facility(code, ukrdc3, errorsdb, redis)
        _get_and_cache_errors_history(code, errorsdb, redis)
    ukrdc3.close()
    errorsdb.close()


@repeat_every(seconds=settings.cache_dashboard_seconds)
def cache_dash_stats() -> None:
    """FastAPI Utils task to refresh statistics for the admin dashboard"""
    jtrace = JtraceSession()
    redis = get_redis()
    logging.info("Refreshing admin statistics")
    get_workitems_stats(jtrace, redis, refresh=True)
    get_empi_stats(jtrace, redis, refresh=True)
    jtrace.close()


@repeat_every(seconds=settings.cache_channel_seconds)
async def cache_mirth_channel_info() -> None:
    """FastAPI Utils task to refresh Mirth channel info"""
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl, timeout=None
    ) as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel infos")
        await cache_channel_info(mirth, redis)


@repeat_every(seconds=settings.cache_groups_seconds)
async def cache_mirth_channel_groups() -> None:
    """FastAPI Utils task to refresh Mirth channel groups"""
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl, timeout=None
    ) as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel groups")
        await cache_channel_groups(mirth, redis)


@repeat_every(seconds=settings.cache_statistics_seconds)
async def cache_mirth_channel_statistics() -> None:
    """FastAPI Utils task to refresh Mirth channel statistics"""
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl, timeout=None
    ) as mirth:
        await mirth.login(settings.mirth_user, settings.mirth_pass)
        redis = get_redis()
        logging.info("Refreshing Mirth channel statistics")
        await cache_channel_statistics(mirth, redis)

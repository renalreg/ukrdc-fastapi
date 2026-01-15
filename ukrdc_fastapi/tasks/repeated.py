import logging
from datetime import datetime, time, date, timedelta
from concurrent.futures import ThreadPoolExecutor
import asyncio
from sqlalchemy import select
from sqlalchemy.sql.functions import func
from typing import Dict, Any
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis, get_root_task_tracker
from ukrdc_fastapi.dependencies.database import errors_session, ukrdc3_session
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.exceptions import MissingFacilityError
from ukrdc_fastapi.query.facilities import get_facilities
from ukrdc_fastapi.query.facilities.stats import get_facility_dialysis_stats
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.cache import BasicCache, DynamicCacheKey, FacilityCachePrefix
from ukrdc_fastapi.utils.mirth import get_channel_map
from ukrdc_fastapi.utils.records import ABSTRACT_FACILITIES

from .utils import repeat_every

# Shared threadpool for CPU-intensive operations
task_executor = ThreadPoolExecutor(
    max_workers=settings.background_threads, thread_name_prefix="bg_task_"
)


async def _run_in_threadpool(sync_func, *args):
    """Helper to run sync code in threadpool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(task_executor, lambda: sync_func(*args))


@repeat_every(seconds=settings.cache_mirth_channel_seconds)
async def update_channel_id_name_map() -> None:
    """
    Update the in-memory Mirth Channel ID-Name map used by MessageSchema
    to populate the channel_name field from the channel_id field.

    Repeats every `cache_mirth_channel_seconds` seconds, to match the cache expiry time.

    The function runs as a tracked background task.
    """

    async def innerfunc():
        async with mirth_session() as mirth:
            channel_map = await _run_in_threadpool(get_channel_map, mirth, get_redis())
            MessageSchema.channel_id_name_map = channel_map

    task = get_root_task_tracker().create(innerfunc, name="Update Mirth Channel Map")
    return await task.tracked()


@repeat_every(seconds=settings.cache_facilities_list_seconds)
async def update_facilities_cache() -> None:
    """
    Update the cached info and basic counts for all facilities.

    Repeats every `cache_facilities_list_seconds` seconds, to match the cache expiry time.

    The function runs as a tracked background task.
    """

    async def innerfunc():
        await _run_in_threadpool(
            get_facilities,
            ukrdc3_session(),
            errors_session(),
            get_redis(),
            True,  # include_inactive
            True,  # include_empty
        )

    task = get_root_task_tracker().create(innerfunc, name="Update Facilities Cache")
    return await task.tracked()


@repeat_every(seconds=settings.cache_facilities_stats_dialysis_seconds)
async def precalculate_facility_stats_dialysis() -> None:
    """
    Pre-calculate the dialysis stats for all facilities with more than
    `cache_facilities_stats_dialysis_min` records.
    """

    async def innerfunc():
        stats = await _run_in_threadpool(_calculate_stats_sync)

        # Main thread handles Redis
        for facility, data in stats.items():
            cache = BasicCache(
                get_redis(),
                DynamicCacheKey(
                    FacilityCachePrefix.KRT, facility, data["start"], data["end"]
                ),
            )
            if not cache.exists:
                cache.set(
                    data["stats"],
                    expire=settings.cache_facilities_stats_dialysis_seconds,
                )

    task = get_root_task_tracker().create(
        innerfunc, name="Pre-calculate Dialysis Stats"
    )
    return await task.tracked()


def _calculate_stats_sync() -> Dict[str, Dict[str, Any]]:
    """Sync stats calculation (runs in threadpool)"""
    results = {}
    with ukrdc3_session() as ukrdc3:
        stmt = (
            select(
                PatientRecord.sendingfacility,
                PatientRecord.sendingextract,
                func.count(PatientRecord.sendingfacility),
            )
            .where(PatientRecord.sendingfacility.notin_(ABSTRACT_FACILITIES))
            .where(PatientRecord.sendingextract == "UKRDC")
            .group_by(PatientRecord.sendingfacility, PatientRecord.sendingextract)
            .order_by(func.count(PatientRecord.sendingfacility).desc())
        )

        facilities = ukrdc3.execute(stmt).all()

        today = datetime.now().date()
        q_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)

        for row in facilities:
            if row[2] <= settings.cache_facilities_stats_dialysis_min:
                continue

            facility = row[0]
            for end_date in [today, q_start]:
                start_date = end_date - timedelta(days=90)
                try:
                    stats = get_facility_dialysis_stats(
                        ukrdc3,
                        facility,
                        since=datetime.combine(start_date, time.min),
                        until=datetime.combine(end_date, time.max),
                    )
                    results[f"{facility}_{end_date}"] = {
                        "stats": stats,
                        "start": start_date.strftime("%Y-%m-%d"),
                        "end": end_date.strftime("%Y-%m-%d"),
                    }
                except MissingFacilityError as e:
                    logging.error(f"Stats failed for {facility}: {e}")

    return results

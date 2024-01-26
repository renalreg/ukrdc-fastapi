import logging
from sqlalchemy import select

from sqlalchemy.sql.functions import func
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
            id_channel_map = await get_channel_map(mirth, get_redis())

            id_name_map = {key: channel.name for key, channel in id_channel_map.items()}
            MessageSchema.set_channel_id_name_map(id_name_map)

    task = get_root_task_tracker().create(
        innerfunc, name="Update MessageSchema Mirth Channel ID-Name map"
    )
    return await task.tracked()


@repeat_every(seconds=settings.cache_facilities_list_seconds)
async def update_facilities_list() -> None:
    """
    Update the cached info and basic counts for all facilities.

    Repeats every `cache_facilities_list_seconds` seconds, to match the cache expiry time.

    The function runs as a tracked background task.
    """

    async def innerfunc():
        with ukrdc3_session() as ukrdc3, errors_session() as errorsdb:
            get_facilities(
                ukrdc3, errorsdb, get_redis(), include_inactive=True, include_empty=True
            )

    task = get_root_task_tracker().create(
        innerfunc, name="Update root Facilities cache"
    )
    return await task.tracked()


@repeat_every(seconds=settings.cache_facilities_stats_dialysis_seconds)
async def precalculate_facility_stats_dialysis() -> None:
    """
    Pre-calculate the dialysis stats for all facilities with more than
    `cache_facilities_stats_dialysis_min` records.
    """

    async def innerfunc():
        with ukrdc3_session() as ukrdc3:
            # Get all non-abstract facilities with UKRDC/RDA feed records
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

            # Only cache facilities with more than `cache_facilities_stats_dialysis_min` records
            facilities_to_cache = (
                row[0]
                for row in facilities
                if row[2] > settings.cache_facilities_stats_dialysis_min
            )

            # Cache the stats for each facility
            for facility_code in facilities_to_cache:
                cache = BasicCache(
                    get_redis(),
                    DynamicCacheKey(FacilityCachePrefix.KRT, facility_code),
                )
                if not cache.exists:
                    try:
                        cache.set(
                            get_facility_dialysis_stats(ukrdc3, facility_code),
                            expire=settings.cache_facilities_stats_dialysis_seconds,
                        )
                    except MissingFacilityError as e:
                        logging.error(e)

    task = get_root_task_tracker().create(
        innerfunc, name="Pre-calculate per-facility dialysis stats"
    )
    return await task.tracked()

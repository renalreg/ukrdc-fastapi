from typing import Optional
from datetime import datetime
from redis import Redis

from fastapi import APIRouter, Depends, Security, Request, Response
from sqlalchemy.orm import Session
from ukrdc_stats.calculators.demographics import DemographicsStats
from ukrdc_stats.calculators.krt import UnitLevelKRTStats
from ukrdc_fastapi.dependencies.cache import get_redis

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.dependencies.cache import cache_factory
from ukrdc_fastapi.permissions.facilities import assert_facility_permission
from ukrdc_fastapi.query.facilities.stats import (
    get_facility_demographic_stats,
    get_facility_dialysis_stats,
)
from ukrdc_fastapi.utils.cache import (
    DynamicCacheKey,
    FacilityCachePrefix,
)

router = APIRouter(tags=["Facilities/Stats"], prefix="/{code}/stats")


@router.get("/demographics", response_model=DemographicsStats)
def facility_stats_demographics(
    code: str,
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    since: Optional[str] = None,
    until: Optional[str] = None,
):
    """Retreive demographic statistics for a given facility"""
    assert_facility_permission(code, user)

    if since and until:
        cache_key = DynamicCacheKey(
            FacilityCachePrefix.DEMOGRAPHICS, code, since, until
        )
    elif since:
        cache_key = DynamicCacheKey(FacilityCachePrefix.DEMOGRAPHICS, code, since)
    elif until:
        cache_key = DynamicCacheKey(FacilityCachePrefix.DEMOGRAPHICS, code, until)
    else:
        cache_key = DynamicCacheKey(FacilityCachePrefix.KRT, code)

    cache = cache_factory(cache_key)(request=request, response=response, redis=redis)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        from_time = (
            datetime.strptime(since + " 00:00:00", "%Y-%m-%d %H:%M:%S")
            if since
            else None
        )
        to_time = (
            datetime.strptime(until + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            if until
            else None
        )
        # Cache a computed value, and expire after 8 hours
        cache.set(
            get_facility_demographic_stats(
                ukrdc3, code, since=from_time, until=to_time
            ),
            expire=settings.cache_facilities_stats_demographics_seconds,
        )

    # Add response cache headers to the response
    cache.prepare_response()

    return DemographicsStats(**cache.get())


@router.get("/krt", response_model=UnitLevelKRTStats)
def facility_stats_krt(
    code: str,
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    since: Optional[str] = None,
    until: Optional[str] = None,
):
    """Retreive KRT statistics for a given facility"""
    assert_facility_permission(code, user)

    if since and until:
        cache_key = DynamicCacheKey(FacilityCachePrefix.KRT, code, since, until)
    elif since:
        cache_key = DynamicCacheKey(FacilityCachePrefix.KRT, code, since)
    elif until:
        cache_key = DynamicCacheKey(FacilityCachePrefix.KRT, code, until)
    else:
        cache_key = DynamicCacheKey(FacilityCachePrefix.KRT, code)

    cache = cache_factory(cache_key)(request=request, response=response, redis=redis)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        from_time = (
            datetime.strptime(since + " 00:00:00", "%Y-%m-%d %H:%M:%S")
            if since
            else None
        )
        to_time = (
            datetime.strptime(until + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            if until
            else None
        )
        # Cache a computed value, and expire after 8 hours
        cache.set(
            get_facility_dialysis_stats(ukrdc3, code, since=from_time, until=to_time),
            expire=settings.cache_facilities_stats_dialysis_seconds,
        )

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return UnitLevelKRTStats(**cache.get())

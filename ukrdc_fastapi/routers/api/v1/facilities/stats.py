from fastapi import APIRouter, Depends, Security
from redis import Redis
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from ukrdc_fastapi.dependencies import get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities.stats.demographics import (
    FacilityDemographicStats,
    get_facility_stats_demographics,
)
from ukrdc_fastapi.utils.cache import ResponseCache

router = APIRouter(tags=["Facilities/Stats"], prefix="/{code}/stats")


def _get_facility_stats_cache(
    code: str, request: Request, response: Response, redis: Redis = Depends(get_redis)
) -> ResponseCache:
    """
    FastAPI dependency to create a cache object for facility statistics.
    Reads the facility code to generate a cache key.
    Arguments are automatically populated by the FastAPI dependency system.

    Args:
        code (str): Facility code (read from the URL path)
        request (Request): Request object
        response (Response): Response object
        redis (Redis): Redis cache session

    Returns:
        ResponseCache: ResponseCache instance with pre-populated key
    """
    cachekey = f"facilities:demographics:{code}"
    return ResponseCache(redis, cachekey, request, response)


@router.get("/demographics", response_model=FacilityDemographicStats)
def facility_stats_demographics(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(_get_facility_stats_cache),
):
    """Retreive demographic distributions for a given facility"""
    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 8 hours
        cache.set(get_facility_stats_demographics(ukrdc3, code, user), expire=28800)

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return FacilityDemographicStats(**cache.get())

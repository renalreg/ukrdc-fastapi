from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.dependencies.cache import facility_cache_factory
from ukrdc_fastapi.query.facilities.stats.demographics import (
    FacilityDemographicStats,
    get_facility_stats_demographics,
)
from ukrdc_fastapi.utils.cache import ResponseCache

router = APIRouter(tags=["Facilities/Stats"], prefix="/{code}/stats")


@router.get("/demographics", response_model=FacilityDemographicStats)
def facility_stats_demographics(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(facility_cache_factory("demographics")),
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

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_stats.calculators.demographics import DemographicsStats
from ukrdc_stats.calculators.dialysis import UnitLevelDialysisStats

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.dependencies.cache import facility_cache_factory
from ukrdc_fastapi.permissions.facilities import assert_facility_permission
from ukrdc_fastapi.query.facilities.stats import (
    get_facility_demographic_stats,
    get_facility_dialysis_stats,
)
from ukrdc_fastapi.utils.cache import FacilityCachePrefix, ResponseCache

router = APIRouter(tags=["Facilities/Stats"], prefix="/{code}/stats")


@router.get("/demographics", response_model=DemographicsStats)
def facility_stats_demographics(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(
        facility_cache_factory(FacilityCachePrefix.DEMOGRAPHICS)
    ),
):
    """Retreive demographic statistics for a given facility"""
    assert_facility_permission(code, user)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 8 hours
        cache.set(
            get_facility_demographic_stats(ukrdc3, code),
            expire=settings.cache_facilities_stats_demographics_seconds,
        )

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return DemographicsStats(**cache.get())


@router.get("/dialysis", response_model=UnitLevelDialysisStats)
def facility_stats_dialysis(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(
        facility_cache_factory(FacilityCachePrefix.DIALYSIS)
    ),
):
    """Retreive KRT statistics for a given facility"""
    assert_facility_permission(code, user)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 8 hours
        cache.set(
            get_facility_dialysis_stats(ukrdc3, code),
            expire=settings.cache_facilities_stats_dialysis_seconds,
        )

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return UnitLevelDialysisStats(**cache.get())

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities import (
    ErrorHistoryPoint,
    FacilityDetailsSchema,
    FacilitySummarySchema,
    get_errors_history,
    get_facilities,
    get_facility,
)
from ukrdc_fastapi.schemas.facility import FacilitySchema
from ukrdc_fastapi.utils.sort import ObjectSorter, make_object_sorter

router = APIRouter(tags=["Facilities"])


@router.get("/", response_model=list[FacilitySummarySchema])
def facility_list(
    include_empty: bool = False,
    sorter: ObjectSorter = Depends(
        make_object_sorter(
            "FacilityEnum",
            ["id", "statistics.patient_records", "statistics.error_IDs_count"],
        )
    ),
    ukrdc3: Session = Depends(get_ukrdc3),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    facilities = get_facilities(ukrdc3, redis, user, include_empty=include_empty)

    return sorter.sort(facilities)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive information and current status of a particular facility"""
    return get_facility(ukrdc3, errorsdb, redis, code, user)


@router.get("/{code}/error_history", response_model=list[ErrorHistoryPoint])
def facility_errrors_history(
    code: str,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    return get_errors_history(ukrdc3, redis, code, user, since=since, until=until)

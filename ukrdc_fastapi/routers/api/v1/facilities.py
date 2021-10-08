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
    get_errors_history,
    get_facilities,
    get_facility,
)
from ukrdc_fastapi.schemas.facility import FacilitySchema

router = APIRouter(tags=["Facilities"])


@router.get("/", response_model=list[FacilitySchema])
def facility_list(
    ukrdc3: Session = Depends(get_ukrdc3),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    return get_facilities(ukrdc3, redis, user)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    return get_facility(ukrdc3, redis, code, user)


@router.get("/{code}/error_history", response_model=list[ErrorHistoryPoint])
def facility_errrors_history(
    code: str,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    return get_errors_history(
        ukrdc3, errorsdb, redis, code, user, since=since, until=until
    )

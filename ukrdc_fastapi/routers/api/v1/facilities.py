from fastapi import APIRouter, Depends, Security
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities import (
    FacilityDetailsSchema,
    get_facilities,
    get_facility,
)
from ukrdc_fastapi.schemas.facility import FacilitySchema

router = APIRouter(tags=["Facilities"])


@router.get("/", response_model=list[FacilitySchema])
def facility_list(
    ukrdc3: Session = Depends(get_ukrdc3),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user),
):
    """Retreive a list of on-record facilities"""
    return get_facilities(ukrdc3, redis, user)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user),
):
    """Retreive a list of on-record facilities"""
    return get_facility(ukrdc3, errorsdb, redis, code, user)
import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_redis, get_statsdb, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.dependencies.cache import FacilityCachePrefix, facility_cache_factory
from ukrdc_fastapi.permissions.facilities import (
    apply_facility_list_permissions,
    assert_facility_permission,
)
from ukrdc_fastapi.query.facilities import (
    FacilityDetailsSchema,
    FacilityExtractsSchema,
    get_facilities,
    get_facility,
    get_facility_extracts,
)
from ukrdc_fastapi.query.facilities.errors import (
    get_errors_history,
    get_patients_latest_errors,
)
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.sorters import ERROR_SORTER
from ukrdc_fastapi.utils.cache import ResponseCache
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import ObjectSorter, SQLASorter, make_object_sorter

from . import reports, stats

router = APIRouter(tags=["Facilities"])
router.include_router(stats.router)
router.include_router(reports.router)


@router.get("", response_model=list[FacilityDetailsSchema])
def facility_list(
    include_inactive: bool = False,
    include_empty: bool = False,
    sorter: ObjectSorter = Depends(
        make_object_sorter(
            "FacilitySorterEnum",
            [
                "id",
                "statistics.total_patients",
                "statistics.patients_receiving_message_error",
                "data_flow.pkb_out",
                "last_message_received_at",
            ],
        )
    ),
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    facilities = get_facilities(
        ukrdc3,
        errorsdb,
        redis,
        include_inactive=include_inactive,
        include_empty=include_empty,
    )

    # Apply permissions to the list of facilities
    facilities = apply_facility_list_permissions(facilities, user)

    return sorter.sort(facilities)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(facility_cache_factory(FacilityCachePrefix.ROOT)),
):
    """Retreive information and current status of a particular facility"""
    assert_facility_permission(code, user)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 1 hour
        cache.set(get_facility(ukrdc3, errorsdb, code), expire=3600)

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return FacilityDetailsSchema(**cache.get())


@router.get(
    "/{code}/patients_latest_errors",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_MESSAGES))],
)
def facility_patients_latest_errors(
    code: str,
    channel: Optional[list[str]] = QueryParam(None),
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    user: UKRDCUser = Security(auth.get_user()),
    sorter: SQLASorter = Depends(ERROR_SORTER),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    assert_facility_permission(code, user)

    query = get_patients_latest_errors(ukrdc3, errorsdb, code, channels=channel)

    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.FACILITY, code, AuditOperation.READ),
    )

    return paginate(sorter.sort(query))


@router.get("/{code}/error_history", response_model=list[HistoryPoint])
def facility_errrors_history(
    code: str,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statsdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    assert_facility_permission(code, user)

    return get_errors_history(ukrdc3, statsdb, code, since=since, until=until)


@router.get("/{code}/extracts", response_model=FacilityExtractsSchema)
def facility_extracts(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
    cache: ResponseCache = Depends(
        facility_cache_factory(FacilityCachePrefix.EXTRACTS)
    ),
):
    """Retreive extract counts for a particular facility"""
    assert_facility_permission(code, user)

    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 1 hour
        cache.set(get_facility_extracts(ukrdc3, code), expire=3600)

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return FacilityExtractsSchema(**cache.get())

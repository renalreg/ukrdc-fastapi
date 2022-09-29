import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_statsdb, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.dependencies.cache import cache_factory
from ukrdc_fastapi.query.admin import AdminCountsSchema, get_admin_counts
from ukrdc_fastapi.query.stats import get_full_errors_history
from ukrdc_fastapi.query.workitems import get_full_workitem_history
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.utils.cache import ResponseCache

from . import datahealth

router = APIRouter(tags=["Admin"])
router.include_router(datahealth.router, prefix="/datahealth")


@router.get(
    "/workitems_history",
    response_model=list[HistoryPoint],
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.UNIT_ALL,
                ]
            )
        )
    ],
)
def full_workitem_history(
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive basic statistics about recent records"""
    return get_full_workitem_history(jtrace, since, until)


@router.get(
    "/errors_history",
    response_model=list[HistoryPoint],
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_MESSAGES,
                    Permissions.UNIT_ALL,
                ]
            )
        )
    ],
)
def full_errors_history(
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    statsdb: Session = Depends(get_statsdb),
):
    """Retreive basic statistics about recent records"""
    return get_full_errors_history(statsdb, since, until)


@router.get(
    "/counts",
    response_model=AdminCountsSchema,
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_MESSAGES,
                    Permissions.READ_WORKITEMS,
                    Permissions.READ_RECORDS,
                    Permissions.UNIT_ALL,
                ]
            )
        )
    ],
)
def admin_counts(
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    cache: ResponseCache = Depends(cache_factory("admin:counts")),
):
    """Retreive basic counts across the UKRDC"""
    # If no cached value exists, or the cached value has expired
    if not cache.exists:
        # Cache a computed value, and expire after 8 hours
        cache.set(get_admin_counts(ukrdc3, jtrace, errorsdb), expire=28800)

    # Add response cache headers to the response
    cache.prepare_response()

    # Fetch the cached value, coerse into the correct type, and return
    return AdminCountsSchema(**cache.get())

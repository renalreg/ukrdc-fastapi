import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_statssdb, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities import (
    FacilityDetailsSchema,
    FacilitySummarySchema,
    get_errors_history,
    get_facilities,
    get_facility,
    get_patients_latest_errors,
)
from ukrdc_fastapi.query.messages import ERROR_SORTER
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import ObjectSorter, SQLASorter, make_object_sorter

router = APIRouter(tags=["Facilities"])


@router.get("/", response_model=list[FacilitySummarySchema])
def facility_list(
    include_empty: bool = False,
    sorter: ObjectSorter = Depends(
        make_object_sorter(
            "FacilityEnum",
            [
                "id",
                "statistics.total_patients",
                "statistics.patients_receiving_message_error",
            ],
        )
    ),
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statssdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    facilities = get_facilities(ukrdc3, statsdb, user, include_empty=include_empty)

    return sorter.sort(facilities)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statssdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive information and current status of a particular facility"""
    return get_facility(ukrdc3, statsdb, code, user)


@router.get("/{code}/error_history", response_model=list[HistoryPoint])
def facility_errrors_history(
    code: str,
    since: Optional[datetime.date] = None,
    until: Optional[datetime.date] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statssdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    return get_errors_history(ukrdc3, statsdb, code, user, since=since, until=until)


@router.get("/{code}/patients_latest_errors", response_model=Page[MessageSchema])
def facility_patients_latest_errors(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    statsdb: Session = Depends(get_statssdb),
    user: UKRDCUser = Security(auth.get_user()),
    sorter: SQLASorter = Depends(ERROR_SORTER),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    query = get_patients_latest_errors(ukrdc3, errorsdb, statsdb, code, user)
    return paginate(sorter.sort(query))

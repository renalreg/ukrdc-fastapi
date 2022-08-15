import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_statsdb, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.facilities import (
    FacilityDetailsSchema,
    get_facilities,
    get_facility,
)
from ukrdc_fastapi.query.facilities.errors import (
    get_errors_history,
    get_patients_latest_errors,
)
from ukrdc_fastapi.query.messages import ERROR_SORTER
from ukrdc_fastapi.schemas.common import HistoryPoint
from ukrdc_fastapi.schemas.message import MessageSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import ObjectSorter, SQLASorter, make_object_sorter

from . import stats

router = APIRouter(tags=["Facilities"])
router.include_router(stats.router)


@router.get("", response_model=list[FacilityDetailsSchema])
def facility_list(
    include_inactive: bool = False,
    include_empty: bool = False,
    sorter: ObjectSorter = Depends(
        make_object_sorter(
            "FacilityEnum",
            [
                "id",
                "statistics.total_patients",
                "statistics.patients_receiving_message_error",
                "data_flow.pkb_out",
                "latest_message.last_message_received_at",
            ],
        )
    ),
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statsdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive a list of on-record facilities"""
    facilities = get_facilities(
        ukrdc3,
        statsdb,
        user,
        include_inactive=include_inactive,
        include_empty=include_empty,
    )

    return sorter.sort(facilities)


@router.get("/{code}", response_model=FacilityDetailsSchema)
def facility(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    statsdb: Session = Depends(get_statsdb),
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
    statsdb: Session = Depends(get_statsdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    return get_errors_history(ukrdc3, statsdb, code, user, since=since, until=until)


@router.get("/{code}/patients_latest_errors", response_model=Page[MessageSchema])
def facility_patients_latest_errors(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    errorsdb: Session = Depends(get_errorsdb),
    statsdb: Session = Depends(get_statsdb),
    user: UKRDCUser = Security(auth.get_user()),
    sorter: SQLASorter = Depends(ERROR_SORTER),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive time-series new error counts for the last year for a particular facility"""
    query = get_patients_latest_errors(ukrdc3, errorsdb, statsdb, code, user)

    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.FACILITY, code, AuditOperation.READ),
    )

    return paginate(sorter.sort(query))

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Latest, Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_statsdb, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.stats import get_full_errors_history
from ukrdc_fastapi.query.workitems import get_full_workitem_history, get_workitems
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.common import HistoryPoint

from . import datahealth

router = APIRouter(tags=["Admin"])
router.include_router(datahealth.router, prefix="/datahealth")


class AdminCountsSchema(OrmModel):
    open_workitems: int
    UKRDC_records: int
    patients_receiving_errors: int


@router.get(
    "/workitems_history",
    response_model=list[HistoryPoint],
    dependencies=[
        Security(
            auth.permission(
                [
                    Permissions.READ_WORKITEMS,
                    Permissions.UNIT_PREFIX + Permissions.UNIT_WILDCARD,
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
                    Permissions.UNIT_PREFIX + Permissions.UNIT_WILDCARD,
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
                    Permissions.UNIT_PREFIX + Permissions.UNIT_WILDCARD,
                ]
            )
        )
    ],
)
def admin_counts(
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive basic counts across the UKRDC"""
    # TODO: Split query into separate function and add cache
    open_workitems_count = get_workitems(jtrace, user, [1]).count()

    ukrdc_records_count = ukrdc3.query(PatientRecord.ukrdcid).distinct().count()

    patients_receiving_errors_count = (
        errorsdb.query(Latest)
        .join(Message)
        .filter(Message.msg_status == "ERROR")
        .count()
    )

    return AdminCountsSchema(
        open_workitems=open_workitems_count,
        UKRDC_records=ukrdc_records_count,
        patients_receiving_errors=patients_receiving_errors_count,
    )

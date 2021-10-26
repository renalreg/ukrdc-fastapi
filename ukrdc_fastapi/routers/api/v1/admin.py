import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.stats import PatientsLatestErrors

from ukrdc_fastapi.dependencies import get_jtrace, get_statssdb
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.stats import get_full_errors_history
from ukrdc_fastapi.query.workitems import get_full_workitem_history, get_workitems
from ukrdc_fastapi.schemas.admin import AdminCountsSchema
from ukrdc_fastapi.schemas.common import HistoryPoint

router = APIRouter(tags=["Admin"])


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
    statsdb: Session = Depends(get_statssdb),
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
    jtrace: Session = Depends(get_jtrace),
    statsdb: Session = Depends(get_statssdb),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive basic counts across the UKRDC"""
    open_workitems_count = get_workitems(jtrace, user, [1]).count()
    ukrdc_records_count = (
        jtrace.query(MasterRecord)
        .filter(MasterRecord.nationalid_type == "UKRDC")
        .count()
    )
    patients_receiving_errors_count = (
        statsdb.query(PatientsLatestErrors.ni).distinct().count()
    )

    return AdminCountsSchema(
        open_workitems=open_workitems_count,
        UKRDC_records=ukrdc_records_count,
        patients_receiving_errors=patients_receiving_errors_count,
    )

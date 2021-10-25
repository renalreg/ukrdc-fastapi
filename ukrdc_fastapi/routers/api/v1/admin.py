import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_statssdb
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.facilities import ErrorHistoryPoint
from ukrdc_fastapi.query.stats import get_full_errors_history
from ukrdc_fastapi.query.workitems import get_full_workitem_history

router = APIRouter(tags=["Admin"])


@router.get(
    "/workitems_history",
    response_model=list[ErrorHistoryPoint],
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
    response_model=list[ErrorHistoryPoint],
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

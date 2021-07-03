import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.errors import get_error, get_errors
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.errors import ExtendedErrorSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Errors/Messages"])


@router.get(
    "/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_messages(
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: str = "ERROR",
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    return paginate(
        get_errors(
            errorsdb, user, status=status, facility=facility, since=since, until=until
        )
    )


@router.get(
    "/{error_id}/",
    response_model=ExtendedErrorSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_detail(
    error_id: str,
    user: UKRDCUser = Security(auth.get_user),
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive detailed information about a specific error message"""
    return get_error(errorsdb, jtrace, error_id, user)

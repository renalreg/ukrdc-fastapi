import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Facility, Message

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.errors import (
    ErrorSchema,
    ExtendedErrorSchema,
    make_extended_error,
    paginate_error_query,
)
from ukrdc_fastapi.utils.filters.errors import filter_error_messages
from ukrdc_fastapi.utils.paginate import Page

router = APIRouter(tags=["Errors"])


@router.get(
    "/",
    response_model=Page[ErrorSchema],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_messages(
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: str = "ERROR",
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    messages = errorsdb.query(Message)

    messages = filter_error_messages(
        messages, facility, since, until, status, default_since_delta=365
    )

    return paginate_error_query(messages, jtrace)


@router.get(
    "/facilities",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_facilities(
    errorsdb: Session = Depends(get_errorsdb),
):
    # TODO: Filter by permissions
    facilities = errorsdb.query(Facility).all()
    return [item.facility for item in facilities if item]


@router.get(
    "/{error_id}",
    response_model=ExtendedErrorSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_detail(
    error_id: str,
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    error = errorsdb.query(Message).get(error_id)
    if not error:
        raise HTTPException(404, detail="Error record not found")

    return make_extended_error(MessageSchema.from_orm(error), jtrace)

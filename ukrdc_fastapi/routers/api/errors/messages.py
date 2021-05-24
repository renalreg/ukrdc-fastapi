import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.access_models.errorsdb import MessageAM
from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.errors import ExtendedErrorSchema, make_extended_error
from ukrdc_fastapi.utils.filters.errors import filter_error_messages
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Errors/Messages"])


@router.get(
    "/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_ERRORS))],
)
def error_messages(
    user: UKRDCUser = Security(auth.get_user),
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: str = "ERROR",
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 365 days.
    """
    messages = errorsdb.query(Message)

    messages = filter_error_messages(
        messages, facility, since, until, status, default_since_delta=365
    )

    messages = MessageAM.apply_query_permissions(messages, user)
    return paginate(messages)


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
    error = errorsdb.query(Message).get(error_id)
    if not error:
        raise HTTPException(404, detail="Error record not found")

    MessageAM.assert_permission(error, user)

    return make_extended_error(MessageSchema.from_orm(error), jtrace)

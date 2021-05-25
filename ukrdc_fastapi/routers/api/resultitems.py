import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import ResultItem

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.resultitems import (
    delete_resultitem,
    get_resultitem,
    get_resultitems,
)
from ukrdc_fastapi.schemas.laborder import ResultItemSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Result Items"])


@router.get(
    "/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def resultitems(
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of lab results, optionally filtered by NI or service ID"""
    return paginate(
        get_resultitems(
            ukrdc3,
            user,
            service_id=service_id,
            order_id=order_id,
            since=since,
            until=until,
        )
    )


@router.get(
    "/{resultitem_id}/",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def resultitem_detail(
    resultitem_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> ResultItem:
    """Retreive a particular lab result"""
    return get_resultitem(ukrdc3, resultitem_id, user)


@router.delete(
    "/{resultitem_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
def resultitem_delete(
    resultitem_id: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
) -> None:
    """Mark a particular lab result for deletion"""
    delete_resultitem(ukrdc3, resultitem_id, user)

import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import LabOrder, ResultItem

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.laborder import ResultItemSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Result Items"])


@router.get(
    "/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def resultitems(
    service_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of lab results, optionally filtered by NI or service ID"""
    query: Query = ukrdc3.query(ResultItem)

    if service_id:
        query = query.filter(ResultItem.service_id.in_(service_id))

    # Optionally filter Workitems updated since
    if since:
        query = query.filter(ResultItem.observation_time >= since)

    # Optionally filter Workitems updated before
    if until:
        query = query.filter(ResultItem.observation_time <= until)

    items = query.order_by(ResultItem.entered_on.desc())
    return paginate(items)


@router.get(
    "/{resultitem_id}/",
    response_model=ResultItemSchema,
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def resultitem_detail(resultitem_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a particular lab result"""
    item = ukrdc3.query(ResultItem).get(resultitem_id)
    if not item:
        raise HTTPException(404, detail="Result item not found")
    return item


@router.delete(
    "/{resultitem_id}/",
    status_code=204,
    dependencies=[Security(auth.permission(Permissions.WRITE_PATIENTRECORDS))],
)
def resultitem_delete(resultitem_id: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Mark a particular lab result for deletion"""
    resultitem: ResultItem = ukrdc3.query(ResultItem).get(resultitem_id)
    if not resultitem:
        raise HTTPException(404, detail="Result item not found")

    logging.info(
        "DELETING: %s %s (%s) - %s%s",
        resultitem.order_id,
        resultitem.service_id,
        resultitem.observation_time,
        resultitem.value,
        resultitem.value_units if resultitem.value_units else "",
    )
    order_id: str = resultitem.order_id
    ukrdc3.delete(resultitem)
    ukrdc3.commit()
    order: LabOrder = ukrdc3.query(LabOrder).get(order_id)
    if order.result_items.count() == 0:
        logging.info(
            "DELETING laborder without any result items: %s %s",
            order.specimen_collected_time,
            order.entered_at,
        )

        ukrdc3.delete(order)
    ukrdc3.commit()

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import LabOrder, PVDelete, ResultItem

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.laborder import ResultItemSchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


class DeleteResultItemsRequestSchema(BaseModel):
    ni: Optional[str]
    service_id: Optional[str]


@router.get(
    "/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def resultitems(
    ni: Optional[str] = None,
    service_id: Optional[str] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of lab results, optionally filtered by NI or service ID"""
    items: Query = ukrdc3.query(ResultItem)
    # Optionally filter by service_id
    if service_id:
        items = items.filter(ResultItem.service_id == service_id)
    # Optionally filter by NI
    if ni:
        items = filters.resultitems_by_ni(ukrdc3, items, ni)
    items = items.order_by(ResultItem.service_id_description)
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
